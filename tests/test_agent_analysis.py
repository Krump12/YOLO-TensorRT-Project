from datetime import datetime, timezone

from src.utils.config import DetectionResult
from src.web.agent_analysis import AgentAnalysisService, build_evidence_packet, severity_from_evidence
from src.web.storage import WebStorage


def test_agent_analysis_builds_evidence_and_severity(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3", clock=lambda: datetime(2026, 5, 11, tzinfo=timezone.utc))
    rows = storage.save_detections(
        [
            DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.8),
            DetectionResult(2, (1, 2, 3, 4), 0, "aphid", 0.9),
        ],
        detected_at=1_700_000_000.0,
        camera_id="cam",
        device_id="dev",
    )

    evidence = build_evidence_packet(rows)

    assert evidence["detection_count"] == 2
    assert evidence["classes"]["aphid"]["count"] == 2
    assert severity_from_evidence(evidence) == "severe"


def test_agent_analysis_service_completes_sync_job(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3", clock=lambda: datetime(2026, 5, 11, tzinfo=timezone.utc))
    storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.8)],
        detected_at=datetime(2026, 5, 11, tzinfo=timezone.utc).timestamp(),
        camera_id="cam",
        device_id="dev",
    )
    service = AgentAnalysisService(storage)

    response = service.start_analysis(async_run=False)
    detail = service.detail(response["analysis_id"])

    assert detail["status"] == "completed"
    assert detail["pest_or_disease_name"] == "aphid"
    assert detail["related_detection_ids"]


def test_agent_analysis_high_risk_trigger_rule(tmp_path):
    service = AgentAnalysisService(WebStorage(tmp_path / "web.sqlite3"), high_risk_min_confidence=0.85, high_risk_min_count=3)

    assert service.should_trigger_high_risk([{"confidence": 0.86}]) is True
    assert service.should_trigger_high_risk([{"confidence": 0.4}, {"confidence": 0.4}, {"confidence": 0.4}]) is True
    assert service.should_trigger_high_risk([{"confidence": 0.4}]) is False
