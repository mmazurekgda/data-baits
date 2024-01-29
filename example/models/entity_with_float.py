from example.databases import databases_with_names, engines
from data_baits.baits import DataModel
from typing import Union


class EntityWithFloatBase:
    name: str
    value: Union[float, None] = None


entity_with_float_on_sqlite = DataModel(
    name="EntityWithFloatOnSQLite",
    database=databases_with_names["test_sqlite"].database_name(),
    model=EntityWithFloatBase,
    engine=engines[databases_with_names["test_sqlite"].database_name()],
)

entity_with_float_on_mysql = DataModel(
    name="EntityWithFloatOnMySQL",
    database=databases_with_names["test_mysql"].database_name(),
    model=EntityWithFloatBase,
    engine=engines[databases_with_names["test_mysql"].database_name()],
)
