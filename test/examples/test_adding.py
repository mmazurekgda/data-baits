from examples.adding_2_floats import add


def test_adding():
    assert add(1, 2) == 3
    assert add(3.5, -4.5) == -1.0
