import numpy as np

from src.utils.config import DetectionResult
from src.visualization.overlay import draw_overlay, rendered_object_count


def test_synthetic_frame_visualization_pipeline():
    frame = np.zeros((108, 192, 3), dtype=np.uint8)
    detections = [DetectionResult(1, (10, 10, 30, 30), 0, "target", 0.95)]
    annotated = draw_overlay(frame, detections, fps=20.0)
    assert annotated.shape == (108, 192, 3)
    assert rendered_object_count(detections) == 1
    assert annotated.sum() > 0
