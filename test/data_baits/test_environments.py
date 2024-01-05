from pydantic import ValidationError
import pytest

trap_base = {
    "name": "my-trap-name",
    "bait": "my-bait-name",
    "namespace": "test-namespace",
    "experiment": "test_experiment_name",
}


def test_empty_environments():
    from data_baits.baits import Trap

    with pytest.raises(ValidationError):
        Trap(**trap_base, environments=[])


def test_valid_environments():
    from data_baits.baits import Trap

    Trap(**trap_base, environments=["env1"])
