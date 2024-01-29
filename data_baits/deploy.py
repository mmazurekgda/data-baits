from datetime import datetime
import kfp
import logging
import click
from kubernetes import (
    client,
    config,
)
import os
from data_baits.bait import Bait
from data_baits.baits import (
    Pipeline,
    Database,
)
from packaging.version import Version
from data_baits.session import get_istio_auth_session
import base64
from data_baits.core.settings import settings


CONFIG_MAP_BODY = {
    "apiVersion": "v1",
    "data": {},
    "kind": "ConfigMap",
    "metadata": {"name": "sniffer-registry"},
    "type": "Opaque",
}


def connect_to_pipeline_api(in_cluster, username, password, endpoint):
    logger = logging.getLogger(settings.LOGGER_NAME)
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
    "--from_secret",
    help=(
        "Use sources from the data-baits-sources "
        "secret or from the path otherwise."
    ),
    default=False,
    is_flag=True,
)
@click.option(
    "--path",
    help="Path where the bait manifests are.",
    type=click.Path(exists=True),
)
@click.option(
    "--in_cluster",
    help="whether to run in cluster",
    callback=deactivate_prompts,
    is_flag=True,
)
@click.option(
    "--rollback",
    help="rollbacks selected baits",
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
def deploy(
    from_secret, path, in_cluster, rollback, username, password, endpoint
):
    logger = logging.getLogger(settings.LOGGER_NAME)
    errors_no = 0
    if not from_secret and not path:
        raise ValueError(
            "You must provide either --path or --from-secret argument!"
        )
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
        body = CONFIG_MAP_BODY.copy()
        body["data"]["first_deployment"] = deployment_time
        registry = v1.create_namespaced_config_map(
            namespace="data-baits",
            body=body,
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

    baits = []
    if from_secret:
        secrets = v1.list_secret_for_all_namespaces(
            label_selector="data-baits-source"
        )
        for secret in secrets.items:
            for encoded_bait in secret.data.values():
                bait = base64.b64decode(encoded_bait.encode("utf-8")).decode(
                    "utf-8"
                )
                bait = Bait.yaml_str_to_bait(bait)
                baits.append(bait)
    else:
        manifest_files = [
            os.path.join(root, file)
            for root, _, files in os.walk(path)
            for file in files
            if file.endswith(".yaml") or file.endswith(".yml")
        ]
        for file in manifest_files:
            with open(file, "r") as f:
                baits.append(Bait.yaml_to_bait(f.name))

    if rollback:
        baits = sorted(baits, key=lambda b: b.version)
        for bait in baits:
            name = bait.id(use_version=False)
            if name in deployed_names:
                if bait.version == deployed_names[name]:
                    passed = True
                    logger.info(
                        f"-> Rolling back bait '{name}' "
                        f"to version '{bait.version}'..."
                    )
                    if isinstance(bait, Pipeline):
                        available_pipelines = kfp_client.list_pipelines(
                            # this will hopefully suffice for now
                            page_size=settings.LIST_PIPELINES_LIMIT,
                        ).pipelines
                        available_pipelines = [
                            p
                            for p in available_pipelines
                            if p.name == bait.name
                        ]
                        if len(available_pipelines) > 1:
                            logger.error(
                                f"There are more than one pipeline with name "
                                f"'{name}'. This should not happen."
                            )
                            passed = False
                            continue
                        if len(available_pipelines) == 0:
                            logger.error(
                                f"There are no pipelines with name "
                                f"'{name}'. This should not happen."
                            )
                            passed = False
                            continue
                        versioned_pipelines = (
                            kfp_client.list_pipeline_versions(
                                pipeline_id=available_pipelines[0].id,
                                page_size=settings.LIST_PIPELINES_LIMIT,
                            ).versions
                        )
                        exact_pipelines = [
                            p
                            for p in versioned_pipelines
                            if p.name == str(bait.version)
                        ]
                        if len(exact_pipelines) == 1:
                            passed &= Pipeline.rollback(
                                exact_pipelines[0].id,
                                kfp_client,
                                use_version=True,
                            )
                        if (
                            len(versioned_pipelines) == 2
                            and versioned_pipelines[0].name == bait.name
                        ):
                            passed &= Pipeline.rollback(
                                versioned_pipelines[0].id,
                                kfp_client,
                                use_version=False,
                            )
                    elif issubclass(type(bait), Database):
                        passed &= type(bait).rollback(
                            bait.database_name(),
                            namespace=bait.namespace,
                        )
                    errors_no += not passed
                    if passed:
                        deployed_baits.pop(
                            f"{bait.id(use_version=False)}_{bait.version}"
                        )
            else:
                logger.info(
                    f"-> Bait '{name}' with version "
                    f"'{bait.version}' was never deployed, skipping..."
                )
        logger.info("-> Updating the registry...")
        print(deployed_baits)
        v1.delete_namespaced_config_map(
            name="sniffer-registry",
            namespace="data-baits",
        )
        body = CONFIG_MAP_BODY.copy()
        body["data"] = deployed_baits
        v1.create_namespaced_config_map(
            namespace="data-baits",
            body=body,
        )
        if errors_no > 0:
            logger.error(
                "Deployment finished with error(s). "
                "Please check the logs for details."
            )
        logger.info("Done!")
        return
    logger.debug("-> Checking if there are new baits to deploy...")
    new_baits = []
    # sort baits by version to make sure that the oldest are deployed first
    baits = sorted(baits, key=lambda b: b.version)
    for bait in baits:
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
        new_databases = []
        for bait in new_baits:
            if isinstance(bait, Pipeline):
                new_pipelines.append(bait)
            elif issubclass(type(bait), Database):
                new_databases.append(bait)
            else:
                logger.warning(
                    f"Found a bait of type '{bait.type}', "
                    "but its deployment is not supported yet."
                )

        available_pipelines = kfp_client.list_pipelines(
            # this will hopefully suffice for now
            page_size=settings.LIST_PIPELINES_LIMIT,
        )
        if len(available_pipelines.pipelines) > settings.LIST_PIPELINES_LIMIT:
            raise ValueError(
                f"There are more than {settings.LIST_PIPELINES_LIMIT} "
                "pipelines in the cluster, which must be increased."
            )
        available_pipelines_names = [
            p.name for p in available_pipelines.pipelines
        ]
        for pipeline in new_pipelines:
            logger.info(
                f"-> Deploying new pipeline '{pipeline.id()}'"
                f" with version '{pipeline.version}'..."
            )
            passed = True
            if pipeline.name not in available_pipelines_names:
                passed = pipeline.deploy(kfp_client, use_version=False)
                available_pipelines_names.append(pipeline.name)
            if passed:
                passed = pipeline.deploy(kfp_client, use_version=True)
            errors_no += not passed
            if passed:
                deployed_baits[
                    f"{pipeline.id(use_version=False)}_{pipeline.version}"
                ] = datetime.utcnow()
        for database in new_databases:
            logger.info(
                f"-> Deploying new database '{database.id()}'"
                f" with version '{database.version}'..."
            )
            passed = database.deploy()
            errors_no += not passed
            if passed:
                deployed_baits[
                    f"{database.id(use_version=False)}_{database.version}"
                ] = datetime.utcnow()
        logger.info("-> Updating the registry...")
        v1.patch_namespaced_config_map(
            name="sniffer-registry",
            namespace="data-baits",
            body={"data": deployed_baits},
        )
    else:
        logger.info("-> No new baits to deploy!")
    if errors_no > 0:
        logger.error(
            "Deployment finished with error(s). "
            "Please check the logs for details."
        )
        exit(1)
    logger.info("Done!")
