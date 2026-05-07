from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml


@dataclass
class ModelArtifact:
    path: Path
    input_size: int = 640
    class_names: dict[int, str] = field(default_factory=dict)
    source_format: str = "pt"

    @property
    def exists(self) -> bool:
        return self.path.is_file()

    def validate(self) -> None:
        if self.path.suffix != ".pt":
            raise ValueError(f"model path must end with .pt: {self.path}")
        if not self.exists:
            raise FileNotFoundError(f"model file not found: {self.path}")
        if self.input_size <= 0:
            raise ValueError("input size must be positive")


@dataclass
class InferenceArtifact:
    path: Path
    precision: str = "fp16"
    source_model_path: Path | None = None
    device: str = "cuda:0"
    load_status: str = "missing"

    def validate_path(self) -> None:
        if self.path.suffix != ".engine":
            raise ValueError(f"engine path must end with .engine: {self.path}")


@dataclass
class CameraStream:
    sensor_id: int = 0
    width: int = 1920
    height: int = 1080
    fps: int = 30
    flip_method: int = 0
    pipeline: str = ""
    connected: bool = False
    last_frame_time: float = 0.0
    dropped_frames: int = 0

    def validate(self) -> None:
        if self.width <= 0 or self.height <= 0:
            raise ValueError("camera width and height must be positive")
        if self.fps <= 0:
            raise ValueError("camera fps must be positive")


@dataclass
class FramePacket:
    frame_id: int
    timestamp: float
    image: Any
    source_width: int
    source_height: int


@dataclass
class DetectionResult:
    frame_id: int
    bbox: tuple[int, int, int, int]
    class_id: int
    class_name: str
    confidence: float

    def clipped(self, width: int, height: int) -> "DetectionResult":
        x1, y1, x2, y2 = self.bbox
        bbox = (
            max(0, min(width - 1, int(x1))),
            max(0, min(height - 1, int(y1))),
            max(0, min(width - 1, int(x2))),
            max(0, min(height - 1, int(y2))),
        )
        return DetectionResult(self.frame_id, bbox, self.class_id, self.class_name, float(self.confidence))


@dataclass
class RuntimeMetrics:
    fps: float = 0.0
    object_count: int = 0
    capture_latency_ms: float = 0.0
    inference_latency_ms: float = 0.0
    display_latency_ms: float = 0.0
    memory_mb: float = 0.0
    started_at: float = 0.0


@dataclass
class AppConfig:
    model_path: Path
    engine_path: Path
    classes_path: Path
    camera: CameraStream
    imgsz: int = 640
    precision: str = "fp16"
    conf_threshold: float = 0.25
    iou_threshold: float = 0.45
    max_detections: int = 300
    queue_size: int = 2
    window_name: str = "YOLO TensorRT Detection"
    exit_key: str = "q"
    log_level: str = "INFO"
    memory_check_interval_sec: float = 5.0
    target_fps: float = 20.0
    max_startup_seconds: float = 10.0
    max_exit_seconds: float = 2.0
    memory_growth_mb_limit: float = 128.0

    def validate(self) -> None:
        self.camera.validate()
        if not 0.0 <= self.conf_threshold <= 1.0:
            raise ValueError("conf_threshold must be between 0.0 and 1.0")
        if not 0.0 <= self.iou_threshold <= 1.0:
            raise ValueError("iou_threshold must be between 0.0 and 1.0")
        if self.queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        if self.imgsz <= 0:
            raise ValueError("imgsz must be positive")


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    if not isinstance(data, dict):
        raise ValueError(f"configuration root must be a mapping: {path}")
    return data


def load_class_names(path: str | Path) -> dict[int, str]:
    path = Path(path)
    if not path.exists():
        return {}
    data = _read_yaml(path)
    names = data.get("names", data)
    if isinstance(names, list):
        return {i: str(name) for i, name in enumerate(names)}
    if isinstance(names, dict):
        return {int(k): str(v) for k, v in names.items()}
    raise ValueError("class names must be a list or mapping")


def load_config(path: str | Path) -> AppConfig:
    path = Path(path)
    data = _read_yaml(path)
    model = data.get("model", {})
    camera_data = data.get("camera", {})
    inference = data.get("inference", {})
    runtime = data.get("runtime", {})
    config = AppConfig(
        model_path=Path(model.get("pt_path", "models/best.pt")),
        engine_path=Path(model.get("engine_path", "models/best.engine")),
        classes_path=Path(model.get("classes_path", "configs/classes.yaml")),
        camera=CameraStream(
            sensor_id=int(camera_data.get("sensor_id", 0)),
            width=int(camera_data.get("width", 1920)),
            height=int(camera_data.get("height", 1080)),
            fps=int(camera_data.get("fps", 30)),
            flip_method=int(camera_data.get("flip_method", 0)),
        ),
        imgsz=int(inference.get("imgsz", 640)),
        precision=str(inference.get("precision", "fp16")),
        conf_threshold=float(inference.get("conf_threshold", 0.25)),
        iou_threshold=float(inference.get("iou_threshold", 0.45)),
        max_detections=int(inference.get("max_detections", 300)),
        queue_size=int(runtime.get("queue_size", 2)),
        window_name=str(runtime.get("window_name", "YOLO TensorRT Detection")),
        exit_key=str(runtime.get("exit_key", "q")),
        log_level=str(runtime.get("log_level", "INFO")),
        memory_check_interval_sec=float(runtime.get("memory_check_interval_sec", 5)),
        target_fps=float(runtime.get("target_fps", 20)),
        max_startup_seconds=float(runtime.get("max_startup_seconds", 10)),
        max_exit_seconds=float(runtime.get("max_exit_seconds", 2)),
        memory_growth_mb_limit=float(runtime.get("memory_growth_mb_limit", 128)),
    )
    config.validate()
    return config
