from data_baits.defaults import K8_NAMESPACE
from data_baits.bait import Bait
from pydantic import field_validator
from typing_extensions import Literal


class Trap(Bait):
    type: Literal["Trap"] = "Trap"
    bait: str
    experiment: str
    namespace: str = K8_NAMESPACE
    ignore: bool = False

    def id(self, *args, **kwargs) -> str:
        return (
            f"{super().id(*args, **kwargs)}-{self.experiment}-{self.namespace}"
        )

    @field_validator("bait", "experiment", "namespace")
    def validate_trap_k8_name(cls, v):
        return cls.parse_k8_name(v)
