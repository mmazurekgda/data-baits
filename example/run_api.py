from data_baits.api.app import create_api_app
import uvicorn

from .models import data_models


def run_api(**kwargs):
    app = create_api_app(
        data_models=data_models,
    )

    uvicorn.run(app, **kwargs)


if __name__ == "__main__":
    # for development only
    run_api(
        port=8000,
    )
