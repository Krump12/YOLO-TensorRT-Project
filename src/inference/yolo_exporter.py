from __future__ import annotations

from pathlib import Path
from typing import Any

from src.utils.config import AppConfig, ModelArtifact, load_class_names
from src.utils.logging import ErrorCategory, RuntimeErrorInfo


def validate_model_artifact(config: AppConfig) -> ModelArtifact:
    class_names = load_class_names(config.classes_path)
    artifact = ModelArtifact(path=config.model_path, input_size=config.imgsz, class_names=class_names)
    artifact.validate()
    return artifact


def select_precision(requested: str, platform_has_fast_fp16: bool = True) -> str:
    requested = requested.lower()
    if requested == "fp16" and platform_has_fast_fp16:
        return "fp16"
    if requested in {"fp16", "fp32"}:
        return "fp32"
    raise ValueError("precision must be fp16 or fp32")


def export_options(config: AppConfig, platform_has_fast_fp16: bool = True) -> dict[str, Any]:
    precision = select_precision(config.precision, platform_has_fast_fp16)
    return {
        "format": "engine",
        "imgsz": config.imgsz,
        "half": precision == "fp16",
        "device": 0,
    }


def export_engine(config: AppConfig, force: bool = False) -> Path:
    validate_model_artifact(config)
    config.engine_path.parent.mkdir(parents=True, exist_ok=True)
    if config.engine_path.exists() and not force:
        return config.engine_path
    try:
        from ultralytics import YOLO

        model = YOLO(str(config.model_path))
        exported = Path(model.export(**export_options(config)))
        if exported.resolve() != config.engine_path.resolve():
            exported.replace(config.engine_path)
        return config.engine_path
    except Exception as exc:
        raise RuntimeErrorInfo(
            ErrorCategory.EXPORT,
            f"failed to export TensorRT engine from {config.model_path}: {exc}",
            "check model compatibility, TensorRT installation, and Jetson environment",
        ) from exc
