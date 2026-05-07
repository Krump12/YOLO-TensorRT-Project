import time

import numpy as np

from src.camera.frame_reader import LatestFrameReader


class FakeCamera:
    def __init__(self):
        self.value = 0
        self.released = False

    def read(self):
        self.value += 1
        time.sleep(0.001)
        return np.full((2, 2, 3), self.value, dtype=np.uint8)

    def release(self):
        self.released = True


def test_latest_frame_reader_returns_recent_frame_and_releases():
    camera = FakeCamera()
    reader = LatestFrameReader(camera, queue_size=1)
    reader.start()
    time.sleep(0.02)
    packet = reader.read_latest(timeout=1)
    reader.stop()
    assert packet is not None
    assert packet.frame_id >= 1
    assert reader.dropped_frames >= 0
    assert camera.released
