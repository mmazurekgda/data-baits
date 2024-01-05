import tempfile
from ruamel.yaml import YAML


def test_writing_core_traps_to_yaml():
    from data_baits.baits import Trap

    trap = Trap(
        name="My Trap Name :)",
        bait="my-bait-name",
        namespace="test-namespace",
        version="1.0",
        experiment="test_experiment_name",
        environments=["env1", "env2"],
        ignore=True,
    )
    with tempfile.NamedTemporaryFile() as f:
        trap.dump_to_yaml(f.name)
        yaml = YAML()
        f.seek(0)
        data = yaml.load(f)
        assert data == {
            "name": "my-trap-name",
            "namespace": "test-namespace",
            "experiment": "test-experiment-name",
            "environments": ["env1", "env2"],
            "ignore": True,
            "bait": "my-bait-name",
            "type": "Trap",
            "version": "1.0",
        }
