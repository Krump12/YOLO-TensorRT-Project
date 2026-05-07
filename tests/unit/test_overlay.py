import numpy as np

from src.utils.config import DetectionResult
from src.visualization.overlay import draw_overlay, format_label


def test_format_label_includes_class_and_confidence():
    det = DetectionResult(1, (1, 1, 3, 3), 9, "unknown:9", 0.876)
    assert format_label(det) == "unknown:9 0.88"


def test_draw_overlay_changes_frame_pixels():
    frame = np.zeros((80, 80, 3), dtype=np.uint8)
    det = DetectionResult(1, (5, 5, 20, 20), 0, "target", 0.9)
    out = draw_overlay(frame, [det], fps=21.5)
    assert out.sum() > 0
