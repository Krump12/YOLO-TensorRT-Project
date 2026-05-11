from __future__ import annotations

import threading
from datetime import timedelta
from typing import Any

from src.web.storage import WebStorage


def build_evidence_packet(
    detections: list[dict[str, object]],
    *,
    crop_stage: str | None = None,
    environment: dict[str, object] | None = None,
) -> dict[str, object]:
    by_class: dict[str, dict[str, object]] = {}
    for detection in detections:
        class_name = str(detection["class_name"])
        item = by_class.setdefault(class_name, {"count": 0, "max_confidence": 0.0, "detection_ids": []})
        item["count"] = int(item["count"]) + 1
        item["max_confidence"] = max(float(item["max_confidence"]), float(detection["confidence"]))
        item["detection_ids"].append(detection["detection_id"])
    return {
        "detection_count": len(detections),
        "classes": by_class,
        "crop_stage": crop_stage,
        "environment": environment or {},
        "time_distribution": [d["detected_at"] for d in detections[:20]],
    }


def severity_from_evidence(evidence: dict[str, object]) -> str:
    count = int(evidence.get("detection_count", 0))
    max_confidence = 0.0
    for item in dict(evidence.get("classes", {})).values():
        max_confidence = max(max_confidence, float(item.get("max_confidence", 0.0)))
    if count >= 10 or max_confidence >= 0.9:
        return "severe"
    if count >= 3 or max_confidence >= 0.75:
        return "moderate"
    return "light"


class AgentAnalysisService:
    def __init__(
        self,
        storage: WebStorage,
        *,
        high_risk_min_confidence: float = 0.85,
        high_risk_min_count: int = 3,
    ) -> None:
        self.storage = storage
        self.high_risk_min_confidence = float(high_risk_min_confidence)
        self.high_risk_min_count = int(high_risk_min_count)
        self._lock = threading.RLock()
        self._running: set[str] = set()

    def should_trigger_high_risk(self, detections: list[dict[str, object]]) -> bool:
        if len(detections) >= self.high_risk_min_count:
            return True
        return any(float(item.get("confidence", 0.0)) >= self.high_risk_min_confidence for item in detections)

    def start_analysis(
        self,
        *,
        hours: int = 48,
        trigger_type: str = "manual",
        crop_stage: str | None = None,
        environment: dict[str, object] | None = None,
        async_run: bool = True,
    ) -> dict[str, object]:
        now = self.storage.clock()
        analysis = self.storage.create_analysis(
            time_range_start=(now - timedelta(hours=max(1, min(48, int(hours))))).isoformat(),
            time_range_end=now.isoformat(),
            trigger_type=trigger_type,
            status="pending",
            severity="light",
            conclusion="",
            evidence={},
            recommendation="",
            need_manual_review=True,
        )
        if async_run:
            thread = threading.Thread(
                target=self._run_analysis,
                args=(analysis["analysis_id"], hours, crop_stage, environment),
                name=f"agent-analysis-{analysis['analysis_id']}",
                daemon=True,
            )
            thread.start()
        else:
            self._run_analysis(str(analysis["analysis_id"]), hours, crop_stage, environment)
        return {"analysis_id": analysis["analysis_id"], "status": analysis["status"]}

    def maybe_trigger_high_risk(self, detections: list[dict[str, object]]) -> None:
        if detections and self.should_trigger_high_risk(detections):
            self.start_analysis(trigger_type="high_risk", async_run=True)

    def _run_analysis(
        self,
        analysis_id: str,
        hours: int,
        crop_stage: str | None,
        environment: dict[str, object] | None,
    ) -> None:
        with self._lock:
            if analysis_id in self._running:
                return
            self._running.add(analysis_id)
        try:
            self.storage.update_analysis(analysis_id, status="running")
            detections = self.storage.recent_detections(hours=hours)
            evidence = build_evidence_packet(detections, crop_stage=crop_stage, environment=environment)
            related_ids = [str(item["detection_id"]) for item in detections]
            if not detections:
                result = {
                    "analysis_time": self.storage.clock().isoformat(),
                    "pest_or_disease_name": None,
                    "severity": "light",
                    "conclusion": "No pest or disease evidence found in recent detections.",
                    "evidence": evidence,
                    "recommendation": "Continue observing and perform manual review if symptoms are visible.",
                    "need_manual_review": True,
                    "related_detection_ids": related_ids,
                    "status": "completed",
                    "error": None,
                }
            else:
                top = max(detections, key=lambda item: float(item["confidence"]))
                severity = severity_from_evidence(evidence)
                result = {
                    "analysis_time": self.storage.clock().isoformat(),
                    "pest_or_disease_name": str(top["class_name"]),
                    "severity": severity,
                    "conclusion": f"{top['class_name']} evidence detected with {len(detections)} recent target records.",
                    "evidence": evidence,
                    "recommendation": "Review affected plants, confirm visually, and apply local integrated pest management guidance.",
                    "need_manual_review": severity in {"moderate", "severe"},
                    "related_detection_ids": related_ids,
                    "status": "completed",
                    "error": None,
                }
            self.storage.update_analysis(analysis_id, **result)
        except Exception as exc:
            self.storage.update_analysis(analysis_id, status="failed", error=str(exc))
        finally:
            with self._lock:
                self._running.discard(analysis_id)

    def recent(self, *, hours: int = 48) -> list[dict[str, object]]:
        return self.storage.recent_analysis(hours=hours)

    def detail(self, analysis_id: str) -> dict[str, object] | None:
        return self.storage.analysis_detail(analysis_id)
