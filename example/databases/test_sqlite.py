from data_baits.baits import SQLiteDatabase
from typing import List

test_sqlite = SQLiteDatabase(
    name="test-sqlite",
    destinations=["example"],
)


def generate() -> List[SQLiteDatabase]:
    return [
        test_sqlite,
    ]
