import time
from pathlib import Path

import numpy as np

from src.utils.config import AppConfig, CameraStream, DetectionResult, FramePacket, WebConfig
from src.web.agent_analysis import AgentAnalysisService
from src.web.storage import WebStorage
from src.web.stream import LatestStateBuffer, WebDetectionPipeline


class Reader:
    def __init__(self, camera, queue_size):
        self.index = 0

    def start(self):
        pass

    def read_latest(self, timeout=0.5):
        if self.index >= 2:
            time.sleep(0.01)
            return None
        self.index += 1
        return FramePacket(self.index, time.time(), np.zeros((8, 8, 3), dtype=np.uint8), 8, 8)

    def stop(self):
        pass


class Detector:
    def detect(self, frame_id, image):
        if frame_id == 1:
            return []
        return [DetectionResult(frame_id, (1, 2, 3, 4), 0, "aphid", 0.9)]


def config():
    return AppConfig(
        model_path=Path("models/best.pt"),
        engine_path=Path("models/best.engine"),
        classes_path=Path("configs/classes.yaml"),
        camera=CameraStream(),
        web=WebConfig(stream_fps=1000),
    )


def test_pipeline_persists_targets_and_ignores_empty_frames(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3")
    state = LatestStateBuffer()
    pipeline = WebDetectionPipeline(
        config(),
        state,
        camera_factory=lambda cfg: object(),
        detector_factory=lambda cfg: Detector(),
        reader_factory=lambda camera, queue_size: Reader(camera, queue_size),
        jpeg_encoder=lambda frame, quality: b"jpeg",
        storage=storage,
    )

    pipeline.start()
    deadline = time.time() + 2
    while not storage.recent_detections() and time.time() < deadline:
        time.sleep(0.01)
    pipeline.stop()

    rows = storage.recent_detections()
    assert len(rows) == 1
    assert rows[0]["class_name"] == "aphid"


def test_agent_analysis_does_not_block_detection_polling(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3")
    storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.9)],
        detected_at=time.time(),
        camera_id="cam",
        device_id="dev",
    )
    service = AgentAnalysisService(storage)

    service.start_analysis(async_run=True)

    assert storage.recent_detections()[0]["class_name"] == "aphid"


def test_chat_today_vs_yesterday_question_gets_grounded_answer(tmp_path):
    from src.web.agent_chat import AgentChatService

    storage = WebStorage(tmp_path / "web.sqlite3")
    storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.9)],
        detected_at=time.time(),
        camera_id="cam",
        device_id="dev",
    )

    answer = AgentChatService(storage).answer(user_id="admin", question="Is today worse than yesterday?", language="en")

    assert answer["related_detection_ids"]
    assert "Conclusion" in answer["answer"]
