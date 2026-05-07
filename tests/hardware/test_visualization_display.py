import pytest

from scripts.run_realtime_detection import main


@pytest.mark.jetson
def test_visualization_display_runs_on_jetson():
    assert main(["--config", "configs/jetson_orin_nano.yaml"]) == 0
