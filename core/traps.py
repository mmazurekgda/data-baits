from pydantic import BaseModel
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as
from pydantic import FilePath
from core.defaults import K8_NAMESPACE, DESTINATIONS
from typing import List
from typing_extensions import Annotated
from pydantic.functional_validators import AfterValidator
import re


def validate_destinations(destinations: List[str]) -> List[str]:
    assert len(destinations) == 0, "Destination list cannot be empty"
    # check if all destinations are valid
    assert all(destination in DESTINATIONS for destination in destinations), (
        f"Invalid destinations: '{destinations}'. "
        "Must be from '{DESTINATIONS}'."
    )
    return destinations


def parse_k8_name(name: str) -> str:
    s = name.lower().strip()
    s = re.sub(r"[^\w\s-]", "", s)
    s = re.sub(r"[\s_-]+", "-", s)
    s = re.sub(r"^-+|-+$", "", s)
    return s


Destinations = Annotated[List[str], AfterValidator(validate_destinations)]
K8Name = Annotated[str, AfterValidator(parse_k8_name)]


class Trap(BaseModel):
    name: K8Name
    experiment_name: K8Name
    namespace: K8Name = K8_NAMESPACE
    destination: Destinations = ["development"]
    ignore: bool = False


class PipelineTrap(Trap):
    bait: str  # not a FilePath because it should be relative

    @staticmethod
    def yaml_to_model(file_path: FilePath) -> "PipelineTrap":
        with FilePath(file_path).open("r") as f:
            content = f.read()
        return parse_yaml_raw_as(PipelineTrap, content)

    def dump_to_yaml(self, file_path: FilePath) -> None:
        with FilePath(file_path).open("w") as f:
            f.write(to_yaml_str(self))
