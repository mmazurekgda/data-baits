from example.databases.test_mysql import test_mysql
from example.databases.test_sqlite import test_sqlite
from sqlalchemy import create_engine


databases = [
    test_mysql,
    test_sqlite,
]

databases_with_names = {db.safe_name(): db for db in databases}

engines = {db.database_name(): create_engine(db.url()) for db in databases}
