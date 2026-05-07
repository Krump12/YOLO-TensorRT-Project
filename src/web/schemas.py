from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Iterable

from src.utils.config import DetectionResult


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def timestamp_iso(timestamp: float | None = None) -> str:
    if timestamp is None:
        return utc_now_iso()
    return datetime.fromtimestamp(float(timestamp), tz=timezone.utc).isoformat()


@dataclass(frozen=True)
class BoundingBoxDTO:
    x1: int
    y1: int
    x2: int
    y2: int

    def to_dict(self) -> dict[str, int]:
        return {"x1": self.x1, "y1": self.y1, "x2": self.x2, "y2": self.y2}


@dataclass(frozen=True)
class DetectionDTO:
    class_id: int
    class_name: str
    confidence: float
    bbox: BoundingBoxDTO

    def to_dict(self) -> dict[str, object]:
        return {
            "class_id": self.class_id,
            "class_name": self.class_name,
            "confidence": self.confidence,
            "bbox": self.bbox.to_dict(),
        }


@dataclass(frozen=True)
class DetectionSnapshotDTO:
    timestamp: str
    fps: float
    target_count: int
    detections: tuple[DetectionDTO, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "timestamp": self.timestamp,
            "fps": self.fps,
            "target_count": self.target_count,
            "detections": [detection.to_dict() for detection in self.detections],
        }


@dataclass(frozen=True)
class RuntimeStatusDTO:
    camera_running: bool
    detector_loaded: bool
    fps: float
    target_count: int
    last_update: str | None = None
    error: str | None = None

    def to_dict(self) -> dict[str, object]:
        return {
            "camera_running": self.camera_running,
            "detector_loaded": self.detector_loaded,
            "fps": self.fps,
            "target_count": self.target_count,
            "last_update": self.last_update,
            "error": self.error,
        }


def detection_to_dto(detection: DetectionResult) -> DetectionDTO:
    x1, y1, x2, y2 = detection.bbox
    confidence = max(0.0, min(1.0, float(detection.confidence)))
    return DetectionDTO(
        class_id=int(detection.class_id),
        class_name=str(detection.class_name),
        confidence=confidence,
        bbox=BoundingBoxDTO(int(x1), int(y1), int(x2), int(y2)),
    )


def snapshot_from_detections(
    detections: Iterable[DetectionResult],
    fps: float = 0.0,
    timestamp: float | str | None = None,
) -> DetectionSnapshotDTO:
    if isinstance(timestamp, str):
        rendered_timestamp = timestamp
    else:
        rendered_timestamp = timestamp_iso(timestamp)
    items = tuple(detection_to_dto(detection) for detection in detections)
    return DetectionSnapshotDTO(
        timestamp=rendered_timestamp,
        fps=float(fps),
        target_count=len(items),
        detections=items,
    )
