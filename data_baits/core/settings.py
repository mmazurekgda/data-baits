from pydantic_settings import BaseSettings, SettingsConfigDict
from enum import Enum
import os
from data_baits import __version__


class Environments(str, Enum):
    dev = "development"
    prod = "production"


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="DATA_BAITS_",
        env_file=os.getenv("DATA_BAITS_ENV_FILE", ".env"),
        extra="allow",
        case_sensitive=True,
    )

    PROJECT_NAME: str = "data-baits"
    PROJECT_VERSION: str = __version__
    DASH_SECRET_KEY: str = ""
    ENVIRONMENT: Environments = Environments.dev.value
    K8_NAMESPACE: str = "github-cd"
    LOGGER_NAME: str = "DB"
    DEFAULT_STORAGE_CLASS: str = "microk8s-hostpath"
    LIST_PIPELINES_LIMIT: int = 1000


settings = Settings()
