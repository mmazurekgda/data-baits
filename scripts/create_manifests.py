import os
import sys
from typing import List
from subprocess import run
import ruamel.yaml
from collections import defaultdict

project_path = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
sys.path.insert(0, project_path)

from data_traps_core.traps import Trap  # noqa
from data_traps_core.defaults import ENVIRONMENTS  # noqa

ignored_files = [
    "__init__.py",
    ".gitkeep",
]


def find_traps() -> List[str]:
    all_files = [
        os.path.join(root, file)
        for root, _, files in os.walk("traps")
        for file in files
        if file not in ignored_files
    ]
    trap_files = [file for file in all_files if file.endswith("trap.yaml")]
    other_files = [file for file in all_files if file not in trap_files]
    print(f"Found {len(trap_files)} trap files.")
    if len(other_files) > 0:
        raise Exception(
            f"Found {len(other_files)} files that "
            f"are not trap files: {other_files}"
        )
    return trap_files


def design_secret(
    env_info: dict,
    trap: Trap,
) -> None:
    secret_name = f"{trap.experiment}-{trap.name}-secret"
    if trap.ignore:
        print("Ignored! Checking if secrets exist...")
        for environment in trap.environments:
            secret_file_path = os.path.join(
                project_path,
                "manifests",
                environment,
                f"{secret_name}.yaml",
            )
            if os.path.exists(secret_file_path):
                print(f"Secret {secret_name} already exists. Removing...")
                os.remove(secret_file_path)
                print("Removed.")
            else:
                print(f"Secret {secret_name} does not exist. Skipping...")
        return
    bait_file_path = os.path.join(
        project_path,
        "baits",
        trap.bait_file,
    )
    bait_file_name = os.path.basename(bait_file_path)
    ex = run(
        [
            "kubectl",
            "create",
            "secret",
            "generic",
            f"{secret_name}",
            "-n",
            f"{trap.namespace}",
            f"--from-file={bait_file_path}",
            f"--namespace={trap.namespace}",
            "--dry-run=client",
            "-o",
            "yaml",
            # ">",
            # f"-o yaml > manifests/{destination}/{secret_name}.yaml",
        ],
        capture_output=True,
        text=True,
    )
    if ex.returncode != 0:
        raise Exception(
            f"Failed to create secret {secret_name} for "
            f"trap {trap.name} in experiment "
            f"{trap.experiment}. Details:"
            f"\n{ex.stderr}\n{ex.stdout}"
        )
    for environment in trap.environments:
        destination_path = os.path.join(
            project_path,
            "manifests",
            environment,
        )
        if not os.path.exists(destination_path):
            os.makedirs(destination_path)
        with open(
            f"{destination_path}/{secret_name}.yaml",
            "w",
        ) as f:
            f.write(ex.stdout)
        container_info = {
            "mount_path": f"/var/run/secrets/{secret_name}",
            "name": secret_name,
            "readOnly": "true",
        }
        volume_info = {
            "secret": {
                "defaultMode": 420,
                "items": {
                    "key": bait_file_name,
                    "path": "secret.yaml",
                },
                "secretName": secret_name,
            },
            "name": secret_name,
        }
        env_info[environment].append(
            {
                "container_info": container_info,
                "volume_info": volume_info,
                "secret_name": secret_name,
            }
        )


def create_pipeline_manifests() -> dict:
    from data_traps_core.pipeline_trap import PipelineTrap

    env_info = defaultdict(list)
    print("Creating pipeline manifests...")
    for pipeline_trap_file in pipeline_trap_files:
        print(f"Creating pipeline manifest for {pipeline_trap_file}...")
        pipeline_trap = PipelineTrap.yaml_to_model(pipeline_trap_file)
        design_secret(
            env_info,
            pipeline_trap,
        )
    return dict(env_info)


if __name__ == "__main__":
    print("Finding traps...")
    trap_files = find_traps()
    pipeline_trap_files = [
        file for file in trap_files if file.endswith("pipeline_trap.yaml")
    ]
    print(f"Found {len(pipeline_trap_files)} pipeline trap files.")
    other_trap_files = [
        file for file in trap_files if file not in pipeline_trap_files
    ]
    if len(other_trap_files) > 0:
        raise Exception(
            f"Found {len(other_trap_files)} files that "
            f"are not recognized trap files: {other_trap_files}"
        )

    pipeline_info = create_pipeline_manifests()

    yaml = ruamel.yaml.YAML()
    with open(f"{project_path}/manifests/base/deployment.yaml") as fp:
        data = yaml.load(fp)

    kustomization_dict = {
        "apiVersion": "kustomize.config.k8s.io/v1beta1",
        "kind": "Kustomization",
        "resources": [
            "../base",
            "deployment.yaml",
        ],
    }

    env_data = defaultdict(lambda: data.copy())
    kus_data = defaultdict(lambda: kustomization_dict.copy())

    for info_source in [
        pipeline_info,
        # add here other info sources
    ]:
        for env, info in pipeline_info.items():
            for single_info in info:
                env_data[env]["spec"]["template"]["spec"]["containers"][0][
                    "volumeMounts"
                ].append(single_info["container_info"])
                env_data[env]["spec"]["template"]["spec"]["volumes"].append(
                    single_info["volume_info"]
                )
                kus_data[env]["resources"].append(
                    f"{single_info['secret_name']}.yaml"
                )

    for env, data in env_data.items():
        with open(
            f"{project_path}/manifests/{env}/deployment.yaml", "w"
        ) as fp:
            yaml.dump(data, fp)

        with open(
            f"{project_path}/manifests/{env}/kustomization.yaml", "w"
        ) as fp:
            yaml.dump(kus_data[env], fp)

    print("Cleaning up...")
    exiles = [env for env in ENVIRONMENTS if env not in env_data.keys()]
    for exile in exiles:
        deployment_path = os.path.join(
            project_path,
            "manifests",
            exile,
            "deployment.yaml",
        )
        if os.path.exists(deployment_path):
            print(f"Removing {deployment_path}...")
            os.remove(deployment_path)
            print("Removed.")
        kustomization_path = os.path.join(
            project_path,
            "manifests",
            exile,
            "kustomization.yaml",
        )
        if os.path.exists(kustomization_path):
            print(f"Removing {kustomization_path}...")
            os.remove(kustomization_path)
            print("Removed.")

    print("Done.")
