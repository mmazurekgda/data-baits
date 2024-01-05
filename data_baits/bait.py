from typing import Any
from pydantic import BaseModel
from pydantic import (
    FilePath,
    field_validator,
    ValidationError,
)
from typing import List
from pydantic_yaml import to_yaml_str, parse_yaml_raw_as
from typing_extensions import Literal
import os
import re
from packaging.version import Version
import importlib


class Bait(BaseModel):
    name: str
    type: Literal["Bait"] = "Bait"
    version: str = str(Version("0.1.0"))
    environments: List[str]

    @staticmethod
    def yaml_to_bait(file_path: FilePath) -> "Bait":
        with open(file_path, "r") as f:
            content = f.read()
        try:
            parsed = parse_yaml_raw_as(Bait, content)
        except ValidationError as e:
            if len(e.errors()) == 1:
                error = e.errors()[0]
                if not (
                    error["type"] == "value_error.const"
                    and error["loc"] == ("__root__", "type")
                ):
                    raise e
                this_type = error["ctx"]["given"]
                requested_bait = getattr(
                    importlib.import_module("core.baits"), this_type
                )
                try:
                    parsed = parse_yaml_raw_as(requested_bait, content)
                except ValidationError:
                    raise ValueError(
                        f"Failed to parse bait with type "
                        f"'{error['input']}' from '{file_path}'."
                    )
            else:
                raise e
        return parsed

    @staticmethod
    def parse_k8_name(name: str) -> str:
        s = name.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        s = re.sub(r"[\s_-]+", "-", s)
        s = re.sub(r"^-+|-+$", "", s)
        if not s:
            raise ValueError("Invalid Kubernetes name: " f"'{name}'. ")
        return s

    @field_validator("name")
    def validate_k8_name(cls, v):
        return cls.parse_k8_name(v)

    @field_validator("environments")
    def validate_environments(cls, envs):
        assert len(envs) != 0, "Destination list cannot be empty"
        return [cls.parse_k8_name(env) for env in envs]

    def dump_to_yaml(
        self, file_path: FilePath, create_path: bool = False
    ) -> None:
        if create_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(to_yaml_str(self))

    def id(self, use_version: bool = True) -> str:
        value = f"{self.type.lower()}-{self.name}"
        if use_version:
            value += f"-{self.version}"
        return value

    def __setattr__(self, name, value):
        if name == "version":
            if not isinstance(value, Version):
                if not isinstance(value, str):
                    value = str(value)
                value = Version(value)
            value = str(value)
        return super().__setattr__(name, value)

    def __getattribute__(self, __name) -> Any:
        value = super().__getattribute__(__name)
        if __name == "version":
            value = Version(value)
        return value
