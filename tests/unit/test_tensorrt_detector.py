from types import SimpleNamespace

import numpy as np

from src.inference.tensorrt_detector import TensorRTDetector, normalize_results


def test_normalize_results_maps_boxes_to_detection_results():
    boxes = SimpleNamespace(xyxy=[[1, 2, 3, 4]], conf=[0.9], cls=[0])
    raw = [SimpleNamespace(boxes=boxes)]
    detections = normalize_results(7, raw, {0: "target"})
    assert len(detections) == 1
    assert detections[0].bbox == (1, 2, 3, 4)
    assert detections[0].class_name == "target"
    assert detections[0].confidence == 0.9


class RecordingModel:
    def __init__(self):
        self.kwargs = None

    def __call__(self, image, **kwargs):
        self.kwargs = kwargs
        boxes = SimpleNamespace(xyxy=[[1, 2, 3, 4]], conf=[0.9], cls=[0])
        return [SimpleNamespace(boxes=boxes)]


def test_detector_passes_configured_predict_options_to_model():
    model = RecordingModel()
    detector = TensorRTDetector(
        "models/best.engine",
        {0: "target"},
        model=model,
        imgsz=640,
        conf=0.1,
        iou=0.5,
        max_det=25,
    )

    detections = detector.detect(1, np.zeros((8, 8, 3), dtype=np.uint8))

    assert len(detections) == 1
    assert model.kwargs == {"verbose": False, "imgsz": 640, "conf": 0.1, "iou": 0.5, "max_det": 25}
