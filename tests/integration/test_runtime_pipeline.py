import numpy as np

from scripts.run_realtime_detection import run_pipeline
from src.utils.config import AppConfig, CameraStream


class FakeCamera:
    def __init__(self):
        self.released = False

    def read(self):
        return np.zeros((4, 4, 3), dtype=np.uint8)

    def release(self):
        self.released = True


class FakeDetector:
    def __init__(self):
        self.calls = 0

    def detect(self, frame_id, image):
        self.calls += 1
        return []


def test_runtime_pipeline_processes_synthetic_frame():
    config = AppConfig(
        model_path="models/best.pt",
        engine_path="models/best.engine",
        classes_path="configs/classes.yaml",
        camera=CameraStream(),
        queue_size=1,
    )
    camera = FakeCamera()
    detector = FakeDetector()
    assert run_pipeline(config, detector=detector, camera=camera, display=None, max_frames=2) == 0
    assert detector.calls == 2
    assert camera.released
