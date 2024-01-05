from datetime import datetime
import kfp
import logging
import click
from kubernetes import (
    client,
    config,
)
from data_baits.defaults import LOGGER_NAME
import os
from data_baits.bait import Bait
from packaging.version import Version
from data_baits.session import get_istio_auth_session
import tempfile
from ruamel.yaml import YAML


def connect_to_pipeline_api(in_cluster, username, password, endpoint):
    logger = logging.getLogger(LOGGER_NAME)
    logger.debug("-> Connecting to the kubeflow pipeline API...")
    if in_cluster:
        kfp_client = kfp.Client()
    else:
        endpoint = endpoint or os.getenv("KUBEFLOW_ENDPOINT")
        if not endpoint:
            raise ValueError(
                "No endpoint provided! Set it as an --endpoint argument or "
                "set the KUBEFLOW_ENDPOINT environment variable!"
            )
        username = username or os.getenv("KUBEFLOW_USERNAME")
        if not username:
            raise ValueError(
                "No username provided! Set it as a --username argument or "
                "set the KUBEFLOW_USERNAME environment variable!"
            )
        password = password or os.getenv("KUBEFLOW_PASSWORD")
        if not password:
            raise ValueError(
                "No password provided! Set it as a --password argument or "
                "set the KUBEFLOW_PASSWORD environment variable!"
            )

        auth_session = get_istio_auth_session(
            url=endpoint,
            username=username,
            password=password,
        )

        kfp_client = kfp.Client(
            host=f"{endpoint}/pipeline", cookies=auth_session["session_cookie"]
        )
    logger.debug("-> Checking if connection is working...")
    healthz = kfp_client.get_kfp_healthz()
    if not getattr(healthz, "multi_user", None):
        raise ValueError(
            "The kfp client is not configured to be multi-user or "
            "something is wrong with the connection!"
        )
    logger.debug("-> Connection is working!")
    return kfp_client


def deactivate_prompts(ctx, _, value):
    for p in ctx.command.params:
        if isinstance(p, click.Option) and p.name == "password":
            if value or os.getenv("KUBEFLOW_PASSWORD"):
                p.prompt = None
    return value


@click.command()
@click.option(
    "--path",
    required=True,
    help="Path where the bait manifests are.",
    type=click.Path(exists=True),
)
@click.option(
    "--in_cluster",
    default=True,
    help="whether to run in cluster",
    callback=deactivate_prompts,
    is_flag=True,
)
@click.option(
    "--username",
    help="Username to access the kfp client",
    required=False,
    type=str,
)
@click.option(
    "--endpoint",
    help="Endpoint `KUBEFLOW_ENDPOINT` of the kfp client",
    required=False,
    type=str,
)
@click.option(
    "--password",
    help="Password for KUBEFLOW_USERNAME to access the kfp client",
    required=False,
    prompt=True,
    hide_input=True,
)
# @click.option(
#     "--path",
#     required=True,
#     help=(
#         "Path where python files with the generate() method are located."
#         "Remember that the generate() method must return a list of "
#         "Baits."
#     ),
#     type=click.Path(exists=True)
# )
def deploy(path, in_cluster, username, password, endpoint):
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("Starting the deployment of data baits...")
    deployment_time: datetime = None
    registry: client.V1ConfigMap = None
    # connect to the cluster
    logger.debug("-> Connecting to the cluster...")
    if in_cluster:
        config.load_incluster_config()
    else:
        config.load_kube_config()
    v1 = client.CoreV1Api()

    # connect to the kubeflow pipeline API
    kfp_client = connect_to_pipeline_api(
        in_cluster, username, password, endpoint
    )

    logger.debug("-> Checking if the registry is already created...")
    try:
        logger.debug("-> Trying to get the registry...")
        registry = v1.read_namespaced_config_map(
            name="sniffer-registry",
            namespace="data-baits",
        )
        logger.debug("-> Registry found!")
        deployment_time = registry.data["first_deployment"]
    except client.exceptions.ApiException:
        logger.debug("-> Registry secret not found!")
        logger.debug("-> Creating the registry secret...")
        deployment_time = datetime.utcnow()
        registry = v1.create_namespaced_config_map(
            namespace="data-baits",
            body={
                "apiVersion": "v1",
                "data": {
                    "first_deployment": deployment_time,
                },
                "kind": "ConfigMap",
                "metadata": {"name": "sniffer-registry"},
                "type": "Opaque",
            },
        )
    logger.info(f"-> Last sniffer deployment time: {deployment_time}")
    logger.debug("-> Getting the list of all deployed baits...")
    deployed_baits = registry.data
    deployed_names = {}
    for bait_name_version, bait_deployed_time in deployed_baits.items():
        if bait_name_version == "first_deployment":
            continue
        name, version = bait_name_version.split("_")
        deployed_names[name] = Version(version)
        logger.debug(
            f"-> '{name}' version '{version}' was "
            f"deployed at {bait_deployed_time}."
        )
    if not deployed_baits:
        logger.debug("-> No deployed baits so far!")

    manifest_files = [
        os.path.join(root, file)
        for root, _, files in os.walk(path)
        for file in files
        if file.endswith(".yaml") or file.endswith(".yml")
    ]

    logger.debug("-> Checking if there are new baits to deploy...")
    new_baits = []
    for file in manifest_files:
        with open(file, "r") as f:
            bait = Bait.yaml_to_bait(f.name)
            name = bait.id(use_version=False)
            if name not in deployed_names:
                logger.debug(
                    f"--> Found a new bait: '{name}'"
                    f" with version '{bait.version}'."
                )
                new_baits.append(bait)
            elif bait.version > deployed_names[name]:
                logger.debug(
                    f"--> Found a newer version of bait: '{name}': "
                    f"{bait.version} > {deployed_names[name]}."
                )
                new_baits.append(bait)
            else:
                logger.debug(
                    f"--> Bait '{name}' with version "
                    f"'{bait.version}' was previously deployed."
                )
    if new_baits:
        logger.info("-> Found new baits to deploy!")
        # pipelines must be deployed first
        new_pipelines = []
        for bait in new_baits:
            if bait.type == "Pipeline":
                new_pipelines.append(bait)
            else:
                raise ValueError(
                    f"Found a bait of type '{bait.type}', "
                    "but its deployment is not supported yet."
                )

        available_pipelines = kfp_client.list_pipelines()
        available_pipelines_names = [
            p.name for p in available_pipelines.pipelines
        ]

        for pipeline in new_pipelines:
            logger.info(
                f"-> Deploying new pipeline '{pipeline.id()}'"
                f" with version '{pipeline.version}'..."
            )
            with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
                yaml = YAML()
                yaml.dump(pipeline.definition, f)
                f.seek(0)
                if pipeline.name not in available_pipelines_names:
                    kfp_client.upload_pipeline(
                        pipeline_package_path=f.name,
                        pipeline_name=pipeline.name,
                        description=pipeline.description,
                    )
                    available_pipelines_names.append(pipeline.name)
                kfp_client.upload_pipeline_version(
                    pipeline_package_path=f.name,
                    pipeline_name=pipeline.name,
                    pipeline_version_name=str(pipeline.version),
                    description=pipeline.description,
                )

        logger.info("-> Updating the registry...")
        for bait in new_baits:
            deployed_baits[
                f"{bait.id(use_version=False)}_{bait.version}"
            ] = datetime.utcnow()

        v1.patch_namespaced_config_map(
            name="sniffer-registry",
            namespace="data-baits",
            body={"data": deployed_baits},
        )
    else:
        logger.info("-> No new baits to deploy!")
    logger.info("Done!")
