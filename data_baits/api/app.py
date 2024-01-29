from fastapi import FastAPI
from data_baits.core.settings import settings
from data_baits.baits.data_model import DataModel
from data_baits.api.api import generate_api_router


def create_api_app(
    data_models: list[DataModel],
) -> FastAPI:
    app = FastAPI(
        title=settings.PROJECT_NAME,
    )

    app.include_router(
        generate_api_router(
            data_models=data_models,
        ),
        prefix="/api",
    )

    return app
