import time
from pathlib import Path

import numpy as np

from src.utils.config import AppConfig, CameraStream, DetectionResult, FramePacket, WebConfig
from src.web.stream import LatestStateBuffer, WebDetectionPipeline


def test_latest_state_buffer_overwrites_without_queue_growth():
    state = LatestStateBuffer()
    for frame_id in range(10):
        state.update(
            frame_id=frame_id,
            source_timestamp=1_700_000_000.0 + frame_id,
            jpeg_bytes=f"frame-{frame_id}".encode(),
            detections=[],
            fps=20.0,
            camera_running=True,
            detector_loaded=True,
        )

    frame = state.latest_frame()
    assert frame is not None
    assert frame.frame_id == 9
    assert frame.jpeg_bytes == b"frame-9"


class FakeReader:
    def __init__(self, camera, queue_size):
        self.camera = camera
        self.queue_size = queue_size
        self.started = False
        self.stopped = False
        self.index = 0

    def start(self):
        self.started = True

    def read_latest(self, timeout=1.0):
        if self.index > 0:
            time.sleep(0.01)
            return None
        self.index += 1
        image = np.zeros((8, 8, 3), dtype=np.uint8)
        return FramePacket(1, 1_700_000_000.0, image, 8, 8)

    def stop(self):
        self.stopped = True
        self.camera.release()


class FakeCamera:
    opens = 0

    def __init__(self):
        self.released = False
        FakeCamera.opens += 1

    def release(self):
        self.released = True


class FakeDetector:
    def __init__(self):
        self.calls = 0

    def detect(self, frame_id, image):
        self.calls += 1
        return [DetectionResult(frame_id, (1, 2, 4, 5), 0, "person", 0.8)]


def test_web_pipeline_reuses_runtime_components_and_publishes_latest_state():
    FakeCamera.opens = 0
    state = LatestStateBuffer()
    detector = FakeDetector()
    config = AppConfig(
        model_path=Path("models/best.pt"),
        engine_path=Path("models/best.engine"),
        classes_path=Path("configs/classes.yaml"),
        camera=CameraStream(),
        queue_size=1,
        web=WebConfig(stream_fps=1000),
    )
    pipeline = WebDetectionPipeline(
        config,
        state,
        camera_factory=lambda cfg: FakeCamera(),
        detector_factory=lambda cfg: detector,
        reader_factory=lambda camera, queue_size: FakeReader(camera, queue_size),
        jpeg_encoder=lambda frame, quality: b"jpeg",
    )

    pipeline.start()
    deadline = time.time() + 2
    while state.latest_frame() is None and time.time() < deadline:
        time.sleep(0.01)
    pipeline.stop()

    assert FakeCamera.opens == 1
    assert detector.calls == 1
    assert state.latest_frame().jpeg_bytes == b"jpeg"
    assert state.latest_detections().target_count == 1
    assert state.status().detector_loaded is True
