from kfp.components.base_component import BaseComponent
from typing import Dict, Any, Optional
from kfp import compiler
from pydantic import FilePath, PrivateAttr
from data_baits.bait import Bait
from typing_extensions import Literal
import tempfile
from ruamel.yaml import YAML


class Pipeline(Bait):
    type: Literal["Pipeline"] = "Pipeline"
    definition: dict = None
    type_check: bool = True
    parameters: Optional[Dict[str, Any]] = None
    description: Optional[str] = None
    _kfp: Optional[BaseComponent] = PrivateAttr(None)

    def __init__(self, *args, kfp_pipeline: BaseComponent = None, **kwargs):
        super().__init__(*args, **kwargs)
        if kfp_pipeline:
            self._kfp = kfp_pipeline

    def set_kfp_pipeline(self, kfp_pipeline: BaseComponent) -> None:
        self._kfp = kfp_pipeline

    def compile(self) -> None:
        if not self._kfp:
            raise AttributeError(
                "You must set the pipeline before compiling the bait."
            )
        with tempfile.NamedTemporaryFile(suffix=".yaml") as f:
            compiler.Compiler().compile(
                pipeline_func=self._kfp,
                package_path=f.name,
                pipeline_name=self.name,
                type_check=self.type_check,
                pipeline_parameters=self.parameters,
            )
            f.seek(0)
            self.__setattr__("definition", YAML().load(f), override=True)

    def __setattr__(self, name, value, override=False):
        if name == "definition" and not override:
            raise AttributeError("definition is read-only")
        return super().__setattr__(name, value)

    def dump_to_yaml(
        self, file_path: FilePath, create_path: bool = False
    ) -> None:
        if not self.definition:
            raise AttributeError(
                "You must compile the bait before dumping it to yaml."
            )
        return super().dump_to_yaml(file_path, create_path)
