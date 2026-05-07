import pytest


@pytest.mark.jetson
def test_memory_stability_on_jetson():
    pytest.skip("Run 30-minute memory validation with pytest --run-jetson on target hardware")
