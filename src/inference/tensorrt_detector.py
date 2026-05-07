from __future__ import annotations

from pathlib import Path
from typing import Any

from src.inference.engine_loader import load_engine
from src.utils.config import DetectionResult


def normalize_results(frame_id: int, raw_results: Any, class_names: dict[int, str] | None = None) -> list[DetectionResult]:
    class_names = class_names or {}
    if raw_results is None:
        return []
    first = raw_results[0] if isinstance(raw_results, (list, tuple)) else raw_results
    boxes = getattr(first, "boxes", None)
    if boxes is None:
        return []
    xyxy = getattr(boxes, "xyxy", [])
    confs = getattr(boxes, "conf", [])
    clss = getattr(boxes, "cls", [])
    detections: list[DetectionResult] = []
    for bbox, conf, cls_id in zip(_to_list(xyxy), _to_list(confs), _to_list(clss)):
        cid = int(cls_id)
        coords = tuple(int(v) for v in _to_list(bbox))
        detections.append(
            DetectionResult(
                frame_id=frame_id,
                bbox=(coords[0], coords[1], coords[2], coords[3]),
                class_id=cid,
                class_name=class_names.get(cid, f"unknown:{cid}"),
                confidence=float(conf),
            )
        )
    return detections


def _to_list(value):
    if hasattr(value, "cpu"):
        value = value.cpu()
    if hasattr(value, "numpy"):
        value = value.numpy()
    if hasattr(value, "tolist"):
        return value.tolist()
    return value


class TensorRTDetector:
    def __init__(
        self,
        engine_path: str | Path,
        class_names: dict[int, str] | None = None,
        model: Any | None = None,
        imgsz: int | None = None,
        conf: float | None = None,
        iou: float | None = None,
        max_det: int | None = None,
    ) -> None:
        self.engine_path = Path(engine_path)
        self.class_names = class_names or {}
        self.model = model
        self.imgsz = imgsz
        self.conf = conf
        self.iou = iou
        self.max_det = max_det

    def load(self) -> "TensorRTDetector":
        if self.model is None:
            self.model = load_engine(self.engine_path)
        return self

    def detect(self, frame_id: int, image: Any) -> list[DetectionResult]:
        if self.model is None:
            self.load()
        raw = self.model(image, **self._predict_kwargs())
        return normalize_results(frame_id, raw, self.class_names)

    def _predict_kwargs(self) -> dict[str, Any]:
        kwargs: dict[str, Any] = {"verbose": False}
        if self.imgsz is not None:
            kwargs["imgsz"] = self.imgsz
        if self.conf is not None:
            kwargs["conf"] = self.conf
        if self.iou is not None:
            kwargs["iou"] = self.iou
        if self.max_det is not None:
            kwargs["max_det"] = self.max_det
        return kwargs
