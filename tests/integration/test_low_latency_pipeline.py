import time

import numpy as np

from scripts.run_realtime_detection import run_pipeline
from src.utils.config import AppConfig, CameraStream


class FastCamera:
    def read(self):
        return np.zeros((4, 4, 3), dtype=np.uint8)

    def release(self):
        pass


class SlowDetector:
    def __init__(self):
        self.calls = 0

    def detect(self, frame_id, image):
        self.calls += 1
        time.sleep(0.01)
        return []


def test_slow_detector_does_not_block_latest_frame_runtime():
    config = AppConfig("models/best.pt", "models/best.engine", "configs/classes.yaml", CameraStream(), queue_size=1)
    detector = SlowDetector()
    assert run_pipeline(config, detector=detector, camera=FastCamera(), max_frames=3) == 0
    assert detector.calls == 3
