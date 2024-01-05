import tempfile
from ruamel.yaml import YAML
from kfp import dsl
import pytest
import os

common_input_attributes = {
    "name": "My Pipeline Name :)",
    "environments": ["env1"],
    "description": "My Pipeline Description :)",
}

common_output_attributes = {
    "name": "my-pipeline-name",
    "type": "Pipeline",
    "type_check": True,
    "version": "0.1.0",
    "environments": ["env1"],
    "description": "My Pipeline Description :)",
}

this_dir = os.path.dirname(__file__)

yaml = YAML()


@dsl.component(base_image="python:3.12")
def empty_component():
    pass


@dsl.pipeline(
    name="empty-pipeline",
    description="empty-pipeline",
)
def multi_component_pipeline():
    empty_component()
    empty_component()


@dsl.component(base_image="python:3.12")
def add(a: float, b: float) -> float:
    return a + b


@dsl.pipeline(
    name="pipeline-with-inputs",
    description="pipeline-with-inputs",
)
def pipeline_with_inputs(a: float, b: float, c: float) -> float:
    result1 = add(a=a, b=b).output
    result2 = add(a=result1, b=c).output
    return result2


@pytest.mark.parametrize(
    "kfp_component,inputs,reference,correct",
    [
        # no pipeline defined
        (None, None, {}, False),
        # single component pipeline
        (
            empty_component,
            None,
            os.path.join(this_dir, "ref/single_component_pipeline.yaml"),
            True,
        ),
        # multi component pipeline
        (
            multi_component_pipeline,
            None,
            os.path.join(this_dir, "ref/multi_component_pipeline.yaml"),
            True,
        ),
        # pipeline with inputs
        (
            pipeline_with_inputs,
            {"a": 1.0, "b": 2.0, "c": 3.0},
            os.path.join(this_dir, "ref/pipeline_with_inputs.yaml"),
            True,
        ),
    ],
)
def test_writing_core_pipelines_to_yaml(
    kfp_component, inputs, reference, correct
):
    def run():
        from data_baits.baits import Pipeline

        pipeline = Pipeline(**common_input_attributes)
        pipeline.parameters = inputs
        pipeline.set_kfp_pipeline(kfp_component)
        if kfp_component:
            pipeline.compile()
        with tempfile.NamedTemporaryFile() as f:
            with open(reference) as fr:
                pipeline.dump_to_yaml(f.name)
                # to get the reference yaml
                # pipeline.dump_to_yaml(f"{pipeline.id()}.yaml")
                f.seek(0)
                data = yaml.load(f)
                ref_definition = yaml.load(fr)
                assert data == {
                    **common_output_attributes,
                    "definition": ref_definition,
                    "parameters": inputs,
                }

    if correct:
        run()
    else:
        with pytest.raises(Exception):
            run()
