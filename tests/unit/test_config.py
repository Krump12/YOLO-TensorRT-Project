from pathlib import Path

import pytest

from tests.conftest import TMP
from src.utils.config import AppConfig, CameraStream, load_class_names, load_config


def test_load_config_valid():
    classes = TMP / "classes.yaml"
    classes.write_text("names:\n  0: person\n", encoding="utf-8")
    cfg = TMP / "config.yaml"
    cfg.write_text(
        f"""
model:
  pt_path: models/best.pt
  engine_path: models/best.engine
  classes_path: {classes.as_posix()}
camera:
  width: 1920
  height: 1080
  fps: 30
inference:
  conf_threshold: 0.5
  iou_threshold: 0.4
runtime:
  queue_size: 2
""",
        encoding="utf-8",
    )
    app = load_config(cfg)
    assert app.model_path == Path("models/best.pt")
    assert app.camera.width == 1920
    assert app.conf_threshold == 0.5
    assert load_class_names(classes) == {0: "person"}


def test_load_config_rejects_invalid_threshold():
    cfg = TMP / "invalid-config.yaml"
    cfg.write_text("inference:\n  conf_threshold: 2\n", encoding="utf-8")
    with pytest.raises(ValueError, match="conf_threshold"):
        load_config(cfg)


def test_app_config_rejects_unbounded_queue():
    app = AppConfig(
        model_path=Path("models/best.pt"),
        engine_path=Path("models/best.engine"),
        classes_path=Path("configs/classes.yaml"),
        camera=CameraStream(),
        queue_size=0,
    )
    with pytest.raises(ValueError, match="queue_size"):
        app.validate()
