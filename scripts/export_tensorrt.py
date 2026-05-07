from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.inference.yolo_exporter import export_engine
from src.utils.config import load_config
from src.utils.logging import ErrorCategory, format_error


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Export YOLO .pt model to TensorRT engine")
    parser.add_argument("--config", default="configs/jetson_orin_nano.yaml")
    parser.add_argument("--model")
    parser.add_argument("--engine")
    parser.add_argument("--imgsz", type=int)
    parser.add_argument("--fp16", action="store_true")
    parser.add_argument("--force", action="store_true")
    return parser


def load_config_with_overrides(args: argparse.Namespace):
    config = load_config(args.config)
    if args.model:
        config.model_path = Path(args.model)
    if args.engine:
        config.engine_path = Path(args.engine)
    if args.imgsz:
        config.imgsz = args.imgsz
    if args.fp16:
        config.precision = "fp16"
    config.validate()
    return config


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        config = load_config_with_overrides(args)
        engine = export_engine(config, force=args.force)
        print(f"TensorRT engine ready: {engine}")
        print(f"Precision requested: {config.precision}")
        return 0
    except Exception as exc:
        info = format_error(exc, ErrorCategory.EXPORT, "check --config, model path, and TensorRT environment")
        print(str(info), file=sys.stderr)
        return info.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
