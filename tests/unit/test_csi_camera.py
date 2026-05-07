from src.camera.csi_camera import build_gstreamer_pipeline
from src.utils.config import CameraStream


def test_gstreamer_pipeline_contains_jetson_csi_settings():
    pipeline = build_gstreamer_pipeline(CameraStream(sensor_id=1, width=1920, height=1080, fps=30, flip_method=2))
    assert "nvarguscamerasrc sensor-id=1" in pipeline
    assert "width=(int)1920" in pipeline
    assert "height=(int)1080" in pipeline
    assert "framerate=(fraction)30/1" in pipeline
    assert "flip-method=2" in pipeline
