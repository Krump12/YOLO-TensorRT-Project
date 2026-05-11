from datetime import datetime, timezone

from src.utils.config import DetectionResult
from src.web.agent_analysis import AgentAnalysisService
from src.web.agent_chat import AgentChatService, build_chat_evidence
from src.web.i18n import translate
from src.web.storage import WebStorage


def test_chat_evidence_counts_detections_and_analyses(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3", clock=lambda: datetime(2026, 5, 11, tzinfo=timezone.utc))
    detections = storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.8)],
        detected_at=datetime(2026, 5, 11, tzinfo=timezone.utc).timestamp(),
        camera_id="cam",
        device_id="dev",
    )
    analysis = AgentAnalysisService(storage)
    analysis.start_analysis(async_run=False)

    evidence = build_chat_evidence(detections, storage.recent_analysis())

    assert evidence["detection_count"] == 1
    assert evidence["analysis_count"] == 1
    assert evidence["class_counts"] == {"aphid": 1}


def test_chat_returns_insufficient_data_when_no_evidence(tmp_path):
    service = AgentChatService(WebStorage(tmp_path / "web.sqlite3"))

    answer = service.answer(user_id="admin", question="Any pests?", language="zh")

    assert answer["answer"] == translate("insufficient_data", "zh")
    assert answer["related_detection_ids"] == []
    assert answer["related_analysis_ids"] == []


def test_chat_answer_is_grounded_with_related_ids(tmp_path):
    now = datetime(2026, 5, 11, tzinfo=timezone.utc)
    storage = WebStorage(tmp_path / "web.sqlite3", clock=lambda: now)
    storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.8)],
        detected_at=now.timestamp(),
        camera_id="cam",
        device_id="dev",
    )

    answer = AgentChatService(storage).answer(user_id="admin", question="What happened?", language="en")

    assert "Conclusion" in answer["answer"]
    assert answer["related_detection_ids"]
