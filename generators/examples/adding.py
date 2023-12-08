def add(a: float, b: float) -> float:
    return a + b


if __name__ == "__main__":
    from kfp import dsl
    import kfp.compiler as compiler

    add_op = dsl.component(
        base_image="python:3.11.5",
    )(add)

    compiler.Compiler().compile(
        add_op,
        "baits/examples/adding.yaml",
        "[Data-Baits Tutorial]Adding",
    )
