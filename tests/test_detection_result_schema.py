from src.utils.config import DetectionResult
from src.web.schemas import BoundingBoxDTO, detection_to_dto, snapshot_from_detections


def test_detection_dto_contains_required_fields():
    detection = DetectionResult(
        frame_id=1,
        bbox=(100, 120, 300, 420),
        class_id=0,
        class_name="person",
        confidence=0.91,
    )

    data = detection_to_dto(detection).to_dict()

    assert data["class_id"] == 0
    assert data["class_name"] == "person"
    assert data["confidence"] == 0.91
    assert data["bbox"] == {"x1": 100, "y1": 120, "x2": 300, "y2": 420}


def test_snapshot_contains_timestamp_fps_count_and_empty_detections():
    snapshot = snapshot_from_detections([], fps=23.5, timestamp=1_700_000_000.0).to_dict()

    assert snapshot["timestamp"].startswith("2023-11-14T")
    assert snapshot["fps"] == 23.5
    assert snapshot["target_count"] == 0
    assert snapshot["detections"] == []


def test_snapshot_from_detection_result():
    detection = DetectionResult(7, (1, 2, 3, 4), 2, "car", 0.5)

    snapshot = snapshot_from_detections([detection], fps=20.0, timestamp="2026-05-07T00:00:00+00:00").to_dict()

    assert snapshot["target_count"] == 1
    assert snapshot["detections"][0]["class_name"] == "car"
    assert snapshot["detections"][0]["bbox"] == BoundingBoxDTO(1, 2, 3, 4).to_dict()
