from data_baits.bait import LogicalBait
from typing_extensions import Literal
from sqlmodel import (
    SQLModel,
    Field,
    Session,
)
from sqlalchemy.engine import Engine
from sqlalchemy.orm import registry
from pydantic import model_validator, ConfigDict
import inflect
from typing import Type
import re


class DBRegistry:
    _instance = None

    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DBRegistry, cls).__new__(
                cls, *args, **kwargs
            )
            cls._instance._registry = {}
        return cls._instance

    def _generate_registry(self, name: str) -> registry:
        class _registry(SQLModel, registry=registry()):
            pass

        _registry.__name__ = name
        return _registry

    def get(self, name: str) -> registry:
        if name not in self._registry:
            self._registry[name] = self._generate_registry(name)
        return self._registry[name]

    def all(self) -> dict[str, registry]:
        return self._registry


class Model:
    pass


class DataModel(LogicalBait):
    type: Literal["DataModel"] = "DataModel"
    name: str = ""
    table_name: str = ""
    database: str  # Field(str, allow_mutation=False)
    model: Type | None = None

    # SQLModel
    _engine: Engine = None
    _sql_model = None
    _sql_model_db = None
    _sql_model_out = None

    model_config = ConfigDict(arbitrary_types_allowed=True)

    def __init__(self, *args, engine: Engine = None, **kwargs):
        super().__init__(*args, **kwargs)
        self._engine = engine
        self._registry = DBRegistry().get(self.database)
        self._sql_model = self.sql_model()
        self._sql_model_db = self.sql_model_db()
        self._sql_model_out = self.sql_model_out()

    @model_validator(mode="after")
    def invent_table_name(self) -> "DataModel":
        if not self.name:
            if self.__class__.__name__ == "DataModel":
                raise ValueError("DataModel must have a name.")
            self.name = self.__class__.__name__
        if self.table_name:
            self.table_name = DataModel.parse_k8_name(
                self.table_name, hyphens=False
            )
        else:
            value = re.sub(r"([A-Z]{2,})", r"_\1", self.name)
            value = re.sub(r"([a-z])([A-Z])", r"\1_\2", value)
            value = DataModel.parse_k8_name(value, hyphens=False)
            value = inflect.engine().plural(value)
            self.table_name = value
        return self

    def sql_model(self) -> SQLModel:
        if not self._sql_model:

            class _klass(self._registry, self.model):
                pass

            _klass.__name__ = self.name.capitalize()
            self._sql_model = _klass
        return self._sql_model

    def sql_model_db(self) -> SQLModel:
        if not self._sql_model_db:

            class _klass_db(self.sql_model(), table=True):
                __tablename__ = self.table_name
                id: int | None = Field(default=None, primary_key=True)

            _klass_db.__name__ = f"{self.name.capitalize()}DB"
            self._sql_model_db = _klass_db
        return self._sql_model_db

    def sql_model_out(self) -> SQLModel:
        if not self._sql_model_out:

            class _klass_out(self.sql_model()):
                id: int

            _klass_out.__name__ = f"{self.name.capitalize()}Out"
            self._sql_model_out = _klass_out
        return self._sql_model_out

    def session(self) -> Session:
        if not self._engine:
            raise ValueError("Engine must be set to use session.")
        return Session(self._engine)
