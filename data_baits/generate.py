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
    CONFIG_MAP_BASE,
    KUSTOMIZATION_BASE,
)
from data_baits.bait import Bait
from pydantic import ValidationError

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
        sources = []
        env_path = os.path.join(path, env)
        if not os.path.exists(env_path):
            logger.debug(f"Creating directory '{env_path}'...")
            os.makedirs(env_path)
        logger.info(f"Dumping bait manifests to '{env_path}'...")

        config_map = CONFIG_MAP_BASE.copy()
        config_map["metadata"]["name"] = f"data-baits-source-{env}"
        config_map["metadata"]["labels"]["data-baits-source"] = env
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
            sources.append(bait_manifest_name)
        yaml = YAML()
        with open(os.path.join(env_path, "config_map.yaml"), "w") as f:
            logger.debug(f"-> Writing a config map manifest to '{f.name}'...")
            config_map["data"]["sources"] = ";".join(sources)
            yaml.dump(config_map, f)
        with open(os.path.join(env_path, "kustomization.yaml"), "w") as f:
            logger.debug(
                f"-> Writing a kustomization manifest to '{f.name}'..."
            )
            yaml.dump(KUSTOMIZATION_BASE, f)
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
@click.pass_context
def generate(
    ctx,
    input_paths: str,
    compile: bool,
    output_path: str,
):
    """Generates baits based on the generate() method."""
    paths = list(set(input_paths))
    env_baits = find_baits(paths, environments=ctx.obj["environments"])
    if compile:
        compile_baits(env_baits)
    if output_path:
        dump_bait_manifests(env_baits, output_path)
