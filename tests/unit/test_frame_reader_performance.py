import time

import numpy as np

from src.camera.frame_reader import LatestFrameReader


class FastCamera:
    def __init__(self):
        self.value = 0

    def read(self):
        self.value += 1
        return np.full((2, 2, 3), self.value % 255, dtype=np.uint8)

    def release(self):
        pass


def test_reader_drops_stale_frames_when_queue_is_full():
    reader = LatestFrameReader(FastCamera(), queue_size=1)
    reader.start()
    time.sleep(0.02)
    packet = reader.read_latest(timeout=1)
    reader.stop()
    assert packet is not None
    assert reader.dropped_frames > 0
