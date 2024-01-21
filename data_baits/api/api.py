from typing import Any

from fastapi import APIRouter
from sqlmodel import select

from data_baits.baits.data_model import DataModel
from fastapi import HTTPException


def generate_create_data_models(
    router: APIRouter,
    data_model: DataModel,
):
    @router.post("/create", response_model=data_model.sql_model_out())
    def _method(*, item_in: data_model.sql_model()) -> Any:
        with data_model.session() as session:
            item = data_model.sql_model_db().model_validate(item_in)
            session.add(item)
            session.commit()
            session.refresh(item)
            return item

    _method.__name__ = f"create_data_model_{data_model.name.replace('-', '_')}"
    return _method


def generate_read_data_models(
    router: APIRouter,
    data_model: DataModel,
):
    @router.get("/", response_model=list[data_model.sql_model_out()])
    def _method(
        skip: int = 0,
        limit: int = 100,
    ) -> Any:
        with data_model.session() as session:
            statement = (
                select(data_model.sql_model_db()).offset(skip).limit(limit)
            )
            return session.exec(statement).all()

    _method.__name__ = f"read_data_models_{data_model.name.replace('-', '_')}"
    return _method


def generate_read_data_model(
    router: APIRouter,
    data_model: DataModel,
):
    @router.get("/{id}", response_model=data_model.sql_model_out())
    def _method(
        id: int,
    ) -> Any:
        with data_model.session() as session:
            model = session.get(data_model.sql_model_db(), id)
            if not model:
                raise HTTPException(
                    status_code=404, detail="DataModel not found!"
                )
            return model

    _method.__name__ = f"read_data_model_{data_model.name.replace('-', '_')}"
    return _method


def generate_api_router(
    data_models: list[DataModel],
) -> APIRouter:
    api_router = APIRouter()

    for data_model in data_models:
        router = APIRouter()

        for generate in [
            generate_read_data_model,
            generate_read_data_models,
            generate_create_data_models,
        ]:
            generate(
                router=router,
                data_model=data_model,
            )

        api_router.include_router(
            router,
            prefix=f"/{data_model.table_name}",
            tags=[data_model.table_name],
        )

    return api_router
