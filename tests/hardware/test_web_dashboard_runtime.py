import pytest


@pytest.mark.jetson
def test_web_dashboard_hardware_runtime_validation():
    pytest.skip(
        "Run on Jetson with real CSI camera: validate 20 FPS Web display, single camera ownership, "
        "<=10% Web overhead, 30-minute memory stability, and graceful shutdown"
    )


@pytest.mark.jetson
def test_agent_dashboard_hardware_runtime_validation():
    pytest.skip(
        "Run on Jetson with real CSI camera: validate continued YOLO inference, continued "
        "target history persistence, and non-blocking Agent analysis/Q&A"
    )
