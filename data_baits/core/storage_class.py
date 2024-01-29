from enum import Enum
from data_baits.core.settings import Settings


class StorageClass(str, Enum):
    default = Settings().DEFAULT_STORAGE_CLASS


class StorageReclaimPolicy(str, Enum):
    delete = "Delete"
    retain = "Retain"
    recycle = "Recycle"
