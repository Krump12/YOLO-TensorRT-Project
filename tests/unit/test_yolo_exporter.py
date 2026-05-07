from pathlib import Path

from src.inference.yolo_exporter import export_options, select_precision
from src.utils.config import AppConfig, CameraStream


def test_select_precision_prefers_fp16_when_supported():
    assert select_precision("fp16", platform_has_fast_fp16=True) == "fp16"


def test_select_precision_falls_back_to_fp32_without_fast_fp16():
    assert select_precision("fp16", platform_has_fast_fp16=False) == "fp32"


def test_export_options_sets_half_for_fp16():
    config = AppConfig(Path("models/best.pt"), Path("models/best.engine"), Path("configs/classes.yaml"), CameraStream())
    options = export_options(config, platform_has_fast_fp16=True)
    assert options["format"] == "engine"
    assert options["half"] is True
