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


class BaitRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(BaitRegistry, cls).__new__(
                cls, *args, **kwargs
            )
            cls._instance._registry = {}
        return cls._instance

    def get(self, name: str, version: str = None) -> dict[str, "Bait"]:
        latest_bait = None
        for bait in self._registry.values():
            if bait.name == name:
                if not version:
                    if not latest_bait:
                        latest_bait = bait
                    elif bait.version > latest_bait.version:
                        latest_bait = bait
                else:
                    if bait.version == version:
                        return bait
        return latest_bait

    def set(self, bait: "Bait") -> None:
        self._registry[bait.id()] = bait

    def all(self) -> dict[str, dict[str, "Bait"]]:
        return self._registry


class GenericBait(BaseModel):
    name: str
    type: Literal["GenericBait"] = "GenericBait"
    version: str = str(Version("0.1.0"))

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

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.id() in BaitRegistry().all():
            raise ValueError(f"Bait with id '{self.id()}' already exists.")
        BaitRegistry().set(self)

    @staticmethod
    def get(name: str) -> "Bait":
        return BaitRegistry().get(name)

    @staticmethod
    def parse_k8_name(name: str, hyphens: bool = True) -> str:
        s = name.lower().strip()
        s = re.sub(r"[^\w\s-]", "", s)
        if hyphens:
            s = re.sub(r"[\s_-]+", "-", s)
        s = re.sub(r"^-+|-+$", "", s)
        if not s:
            raise ValueError("Invalid name: " f"'{name}'. ")
        return s


class LogicalBait(GenericBait):
    type: Literal["LogicalBait"] = "LogicalBait"


class PhysicalBait(GenericBait):
    type: Literal["PhysicalBait"] = "PhysicalBait"
    destinations: List[str]

    def deploy(self, *_, **__) -> bool:
        raise NotImplementedError

    @staticmethod
    def rollback(*_, **__) -> bool:
        raise NotImplementedError

    @staticmethod
    def _yaml_to_bait_core(content: str) -> "Bait":
        try:
            parsed = parse_yaml_raw_as(Bait, content)
        except ValidationError as e:
            if len(e.errors()) == 1:
                error = e.errors()[0]
                if not (
                    error["type"] == "literal_error"
                    and error["loc"] == ("type",)
                ):
                    raise e
                this_type = error["input"]
                requested_bait = getattr(
                    importlib.import_module("data_baits.baits"), this_type
                )
                try:
                    parsed = parse_yaml_raw_as(requested_bait, content)
                except ValidationError:
                    raise ValueError(
                        f"Failed to parse bait with type "
                        f"'{error['input']}'."
                    )
            else:
                raise e
        return parsed

    @staticmethod
    def yaml_to_bait(file_path: FilePath) -> "Bait":
        with open(file_path, "r") as f:
            content = f.read()
        return Bait._yaml_to_bait_core(content)

    @staticmethod
    def yaml_str_to_bait(content: str) -> "Bait":
        return Bait._yaml_to_bait_core(content)

    @field_validator("name")
    def validate_k8_name(cls, v):
        return cls.parse_k8_name(v)

    @field_validator("destinations")
    def validate_destinations(cls, envs):
        assert len(envs) != 0, "Destination list cannot be empty"
        return [cls.parse_k8_name(env) for env in envs]

    def dump_to_yaml(
        self, file_path: FilePath, create_path: bool = False
    ) -> None:
        if create_path:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
        with open(file_path, "w") as f:
            f.write(to_yaml_str(self))

    def dump_to_yaml_str(self) -> str:
        return to_yaml_str(self)


# for backwards compatibility
class Bait(PhysicalBait):
    type: Literal["Bait"] = "Bait"
