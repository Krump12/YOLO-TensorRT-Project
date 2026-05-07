import pytest


@pytest.mark.jetson
def test_realtime_fps_budget_on_jetson():
    pytest.skip("Run manual 1080P FPS validation with pytest --run-jetson after engine export")
