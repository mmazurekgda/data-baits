import os
from ruamel.yaml import YAML
import logging
from typing import List, Dict
from data_baits.baits import Pipeline
from collections import defaultdict
import importlib.util
import click
from data_baits.defaults import (
    LOGGER_NAME,
    SOURCES_SECRET_BASE,
    KUSTOMIZATION_BASE,
    NAMESPACE_BASE,
    SNIFFER_JOB_BASE,
)
from data_baits.bait import Bait
from pydantic import ValidationError
import base64

EnvBaits = Dict[str, List[Bait]]


def compile_baits(env_baits: EnvBaits) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    logger.info("Compiling baits...")
    for baits in env_baits.values():
        for bait in baits:
            if isinstance(bait, Pipeline):
                if bait.definition:
                    logger.debug(
                        f"-> Pipeline '{bait.name}' "
                        "already compiled. Skipping..."
                    )
                else:
                    logger.debug(f"-> Compiling bait '{bait.name}'...")
                    bait.compile()
    logger.info("Done.")


def find_baits(
    paths: List[str],
    environments: List[str],
) -> EnvBaits:
    logger = logging.getLogger(LOGGER_NAME)

    all_files = []
    for path in paths:
        logger.info(f"Scanning for generator files in '{path}'...")
        all_files += [
            os.path.join(root, file)
            for root, _, files in os.walk(path)
            for file in files
            if file.endswith(".py") and file != "__init__.py"
        ]
    generator_files = []
    baits = defaultdict(list)
    name_registry = []
    for file in all_files:
        spec = importlib.util.spec_from_file_location("module.name", file)
        module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(module)
        if hasattr(module, "generate"):
            logger.debug(f"-> Found a generator file '{file}'.")
            local_baits = []
            try:
                local_baits = module.generate()
            except ValidationError as e:
                logger.error(
                    f"Failed to generate baits/traps from '{file}'. "
                    f"Details:\n{e}"
                )
            err_msg = "generate() must return a list of Baits."
            if not isinstance(local_baits, list):
                raise ValueError(err_msg)
            for bait in local_baits:
                if not isinstance(bait, Bait):
                    raise ValueError(err_msg)
                valid_envs = [
                    env for env in bait.environments if env in environments
                ]
                if not valid_envs:
                    logger.warning(
                        f"--> Skipping {bait.type} with id: '{bait.id()}' "
                        "because it is not valid for any of the "
                        f"environments: {environments}"
                    )
                    continue
                logger.debug(
                    f"--> Found {bait.type} with id: '{bait.id()}' "
                    f"for environments: {valid_envs}"
                )
                if bait.id() in name_registry:
                    raise ValueError(
                        f"Found duplicate id '{bait.name}' in '{file}'."
                    )
                name_registry.append(bait.name)
                for env in valid_envs:
                    baits[env].append(bait)
            generator_files.append(file)
        else:
            logger.warning(
                f"-> File '{file}' is not a generator file."
                "It must implement a generate() function."
                "Skipping..."
            )
    other_files = [file for file in all_files if file not in generator_files]
    generator_files_no = len(generator_files)
    logger.debug(f"Processed ({generator_files_no}/{len(all_files)}) files.")
    other_files_no = len(other_files)
    if other_files_no > 0:
        logger.warning(f"Found {other_files_no} without the generate method!")
        for file in other_files:
            logger.warning(f"-> '{file}'")
    logger.info("Done.")
    return baits


def dump_bait_manifests(
    env_baits: EnvBaits,
    path: str,
) -> None:
    logger = logging.getLogger(LOGGER_NAME)
    for env, baits in env_baits.items():
        sources = {}
        env_path = os.path.join(path, env)
        if not os.path.exists(env_path):
            logger.debug(f"Creating directory '{env_path}'...")
            os.makedirs(env_path)
        logger.info(f"Dumping bait manifests to '{env_path}'...")

        secret = SOURCES_SECRET_BASE.copy()
        secret["metadata"]["name"] = f"data-baits-source-{env}"
        secret["metadata"]["labels"]["data-baits-source"] = env
        for bait in baits:
            bait_manifest_name = f"{bait.id()}.yaml"
            destination = os.path.join(
                env_path,
                bait_manifest_name,
            )
            logger.debug(
                f"-> Dumping bait '{bait.id()}' to '{destination}'..."
            )
            bait.dump_to_yaml(
                destination,
                create_path=True,
            )
            with open(destination, "r") as f:
                bait_manifest_str = bait.dump_to_yaml_str()
                sources[bait_manifest_name] = base64.b64encode(
                    bait_manifest_str.encode("utf-8")
                ).decode("utf-8")
        namespaces = ["data-baits"]
        for bait in baits:
            if getattr(bait, "namespace", None):
                namespaces.append(bait.namespace)
        for namespace in namespaces:
            with open(
                os.path.join(env_path, f"{namespace}-namespace.yaml"), "w"
            ) as f:
                logger.debug(
                    f"-> Writing a namespace manifest to '{f.name}'..."
                )
                namespace_manifest = NAMESPACE_BASE.copy()
                namespace_manifest["metadata"]["name"] = namespace
                YAML().dump(namespace_manifest, f)
        with open(os.path.join(env_path, "sources_secret.yaml"), "w") as f:
            logger.debug(f"-> Writing a config map manifest to '{f.name}'...")
            secret["data"] = sources
            YAML().dump(secret, f)
        with open(os.path.join(env_path, "sniffer_job.yaml"), "w") as f:
            logger.debug(f"-> Writing a job manifest to '{f.name}'...")
            YAML().dump(SNIFFER_JOB_BASE, f)
        with open(os.path.join(env_path, "kustomization.yaml"), "w") as f:
            logger.debug(
                f"-> Writing a kustomization manifest to '{f.name}'..."
            )
            kustomization = KUSTOMIZATION_BASE.copy()
            kustomization["resources"] = [
                "sources_secret.yaml",
                "sniffer_job.yaml",
            ]
            kustomization["resources"] += [
                f"{namespace}-namespace.yaml" for namespace in namespaces
            ]
            YAML().dump(kustomization, f)
    logger.info("Done.")


@click.command()
@click.option(
    "--input_paths",
    required=True,
    help=(
        "Paths where python files with the generate() method are located."
        "Remember that the generate() method must return a list of Baits."
    ),
    type=click.Path(exists=True),
    multiple=True,
)
@click.option(
    "--compile",
    help="Compile the pipelines from the found bait manifests.",
    is_flag=True,
    show_default=True,
    default=True,
)
@click.option(
    "--output_path",
    help="Path where the compiled bait elements should be written.",
    type=click.Path(exists=True),
)
@click.option(
    "--environments",
    required=True,
    help="Environments (clusters) to consider.",
    type=str,
    multiple=True,
)
def generate(
    input_paths,
    compile,
    output_path,
    environments,
):
    """Generates baits based on the generate() method."""
    environments = list(set(environments))
    paths = list(set(input_paths))
    env_baits = find_baits(paths, environments)
    if compile:
        compile_baits(env_baits)
    if output_path:
        dump_bait_manifests(env_baits, output_path)
