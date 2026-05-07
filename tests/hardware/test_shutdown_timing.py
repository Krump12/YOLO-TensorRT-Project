import pytest


@pytest.mark.jetson
def test_shutdown_timing_on_jetson():
    pytest.skip("Run shutdown timing validation with pytest --run-jetson on target hardware")
