from kfp import dsl
from typing import List
from data_baits.baits import Pipeline


def add(a: float, b: float) -> float:
    return a + b


def generate() -> List[Pipeline]:
    pipeline_name = "adding-2-floats"
    return [
        Pipeline(
            name=pipeline_name,
            kfp_pipeline=dsl.component(
                base_image="python:3.11.5",
            )(add),
            description="""
            This pipeline adds two floats.
            It is the simplest of examples on how to create a pipeline.
            It consists of just one component.
            """,
            version="0.1.9",
            destinations=["example"],
        ),
    ]
