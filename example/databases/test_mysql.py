from data_baits.baits import MySQLInternalDatabase
from data_baits.core.settings import settings
from typing import List
import os
from data_baits.core.storage_class import StorageReclaimPolicy

test_mysql = MySQLInternalDatabase(
    name="test-mysql",
    destinations=["example"],
    storage="10Gi",
    reclaim_policy=StorageReclaimPolicy.retain,
)
if settings.ENVIRONMENT == "development":
    test_mysql.connector = settings.TEST_MYSQL_CONNECTOR
    test_mysql.host = settings.TEST_MYSQL_HOST
    test_mysql.port = settings.TEST_MYSQL_PORT
    test_mysql.password_env_name = "TEST_MYSQL_PASSWORD"
    os.environ["TEST_MYSQL_PASSWORD"] = settings.TEST_MYSQL_PASSWORD
    test_mysql.user_env_name = "TEST_MYSQL_USERNAME"
    os.environ["TEST_MYSQL_USERNAME"] = settings.TEST_MYSQL_USERNAME


def generate() -> List[MySQLInternalDatabase]:
    return [
        test_mysql,
    ]
