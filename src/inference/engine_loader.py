from __future__ import annotations

from pathlib import Path

from src.utils.config import InferenceArtifact
from src.utils.logging import ErrorCategory, RuntimeErrorInfo


def validate_engine_path(path: str | Path) -> InferenceArtifact:
    artifact = InferenceArtifact(path=Path(path))
    artifact.validate_path()
    if not artifact.path.is_file():
        raise FileNotFoundError(f"engine file not found: {artifact.path}")
    artifact.load_status = "exported"
    return artifact


def load_engine(path: str | Path):
    artifact = validate_engine_path(path)
    try:
        from ultralytics import YOLO

        model = YOLO(str(artifact.path))
        artifact.load_status = "loaded"
        return model
    except Exception as exc:
        raise RuntimeErrorInfo(
            ErrorCategory.ENGINE,
            f"failed to load TensorRT engine {artifact.path}: {exc}",
            "verify the engine was built on this Jetson/TensorRT environment",
        ) from exc
