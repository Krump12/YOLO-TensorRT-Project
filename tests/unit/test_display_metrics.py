from src.utils.config import DetectionResult
from src.visualization.overlay import rendered_object_count


def test_rendered_object_count_matches_boxes():
    detections = [
        DetectionResult(1, (0, 0, 1, 1), 0, "a", 0.8),
        DetectionResult(1, (2, 2, 3, 3), 1, "b", 0.7),
    ]
    assert rendered_object_count(detections) == 2
    assert rendered_object_count([]) == 0
