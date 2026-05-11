from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

try:
    import yaml
except ModuleNotFoundError:  # pragma: no cover - exercised only in minimal test environments
    yaml = None


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
class WebConfig:
    host: str = "0.0.0.0"
    port: int = 8000
    username: str = "admin"
    password_env: str = "YOLO_WEB_PASSWORD"
    stream_fps: float = 20.0
    jpeg_quality: int = 80
    session_secret_env: str = "YOLO_WEB_SESSION_SECRET"
    storage_path: str = "data/web_dashboard.sqlite3"
    device_id: str = "jetson-orin-nano"
    camera_id: str = "csi-0"
    analysis_interval_minutes: int = 60
    high_risk_min_confidence: float = 0.85
    high_risk_min_count: int = 3

    def validate(self) -> None:
        if not self.host:
            raise ValueError("web host must not be empty")
        if not 1 <= int(self.port) <= 65535:
            raise ValueError("web port must be between 1 and 65535")
        if not self.username:
            raise ValueError("web username must not be empty")
        if not self.password_env:
            raise ValueError("web password_env must not be empty")
        if not self.session_secret_env:
            raise ValueError("web session_secret_env must not be empty")
        if self.stream_fps <= 0:
            raise ValueError("web stream_fps must be positive")
        if not 1 <= int(self.jpeg_quality) <= 100:
            raise ValueError("web jpeg_quality must be between 1 and 100")
        if not self.storage_path:
            raise ValueError("web storage_path must not be empty")
        if not self.device_id:
            raise ValueError("web device_id must not be empty")
        if not self.camera_id:
            raise ValueError("web camera_id must not be empty")
        if self.analysis_interval_minutes <= 0:
            raise ValueError("web analysis_interval_minutes must be positive")
        if not 0.0 <= self.high_risk_min_confidence <= 1.0:
            raise ValueError("web high_risk_min_confidence must be between 0.0 and 1.0")
        if self.high_risk_min_count <= 0:
            raise ValueError("web high_risk_min_count must be positive")

    def password(self) -> str:
        return _required_env(self.password_env, "web password")

    def session_secret(self) -> str:
        return _required_env(self.session_secret_env, "web session secret")


def _required_env(name: str, label: str) -> str:
    value = os.environ.get(name, "")
    if not value:
        raise RuntimeError(f"missing required {label} environment variable: {name}")
    return value


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
    web: WebConfig = field(default_factory=WebConfig)

    def validate(self) -> None:
        self.camera.validate()
        self.web.validate()
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
        if yaml is not None:
            data = yaml.safe_load(f) or {}
        else:
            data = _minimal_yaml_load(f.read())
    if not isinstance(data, dict):
        raise ValueError(f"configuration root must be a mapping: {path}")
    return data


def _minimal_yaml_load(text: str) -> dict[str, Any]:
    root: dict[str, Any] = {}
    stack: list[tuple[int, dict[str, Any]]] = [(-1, root)]
    for raw_line in text.splitlines():
        if not raw_line.strip() or raw_line.lstrip().startswith("#"):
            continue
        indent = len(raw_line) - len(raw_line.lstrip(" "))
        key, _, value = raw_line.strip().partition(":")
        while stack and indent <= stack[-1][0]:
            stack.pop()
        parent = stack[-1][1]
        if value.strip() == "":
            child: dict[str, Any] = {}
            parent[key] = child
            stack.append((indent, child))
        else:
            parent[key] = _parse_scalar(value.strip())
    return root


def _parse_scalar(value: str) -> Any:
    lowered = value.lower()
    if lowered in {"true", "false"}:
        return lowered == "true"
    try:
        if "." in value:
            return float(value)
        return int(value)
    except ValueError:
        return value


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
    web = data.get("web", {})
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
        web=WebConfig(
            host=str(web.get("host", "0.0.0.0")),
            port=int(web.get("port", 8000)),
            username=str(web.get("username", "admin")),
            password_env=str(web.get("password_env", "YOLO_WEB_PASSWORD")),
            stream_fps=float(web.get("stream_fps", 20)),
            jpeg_quality=int(web.get("jpeg_quality", 80)),
            session_secret_env=str(web.get("session_secret_env", "YOLO_WEB_SESSION_SECRET")),
            storage_path=str(web.get("storage_path", "data/web_dashboard.sqlite3")),
            device_id=str(web.get("device_id", "jetson-orin-nano")),
            camera_id=str(web.get("camera_id", "csi-0")),
            analysis_interval_minutes=int(web.get("analysis_interval_minutes", 60)),
            high_risk_min_confidence=float(web.get("high_risk_min_confidence", 0.85)),
            high_risk_min_count=int(web.get("high_risk_min_count", 3)),
        ),
    )
    config.validate()
    return config
