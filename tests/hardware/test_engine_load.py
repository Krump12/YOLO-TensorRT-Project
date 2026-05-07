import pytest

from src.inference.engine_loader import load_engine


@pytest.mark.jetson
def test_engine_loads_on_jetson():
    assert load_engine("models/best.engine") is not None
