from example.models.entity_with_float import (
    entity_with_float_on_mysql,
    entity_with_float_on_sqlite,
)
from example.models.user import user

data_models = [
    entity_with_float_on_mysql,
    entity_with_float_on_sqlite,
    user,
]
