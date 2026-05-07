import pytest

from src.camera.csi_camera import CSICamera
from src.utils.config import CameraStream


@pytest.mark.jetson
def test_csi_camera_reads_frame_on_jetson():
    camera = CSICamera(CameraStream()).open()
    try:
        frame = camera.read()
        assert frame is not None
        assert frame.shape[0] > 0
    finally:
        camera.release()
