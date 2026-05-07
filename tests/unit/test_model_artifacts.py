from pathlib import Path

import pytest

from tests.conftest import TMP
from src.inference.yolo_exporter import validate_model_artifact
from src.utils.config import AppConfig, CameraStream


def make_config(model_path: Path, classes_path: Path) -> AppConfig:
    return AppConfig(
        model_path=model_path,
        engine_path=Path("models/best.engine"),
        classes_path=classes_path,
        camera=CameraStream(),
    )


def test_model_validation_loads_class_names():
    model = TMP / "best.pt"
    model.write_bytes(b"fake")
    classes = TMP / "model-classes.yaml"
    classes.write_text("names:\n  0: target\n", encoding="utf-8")
    artifact = validate_model_artifact(make_config(model, classes))
    assert artifact.class_names == {0: "target"}


def test_model_validation_rejects_missing_model():
    with pytest.raises(FileNotFoundError):
        validate_model_artifact(make_config(TMP / "missing.pt", TMP / "classes.yaml"))
