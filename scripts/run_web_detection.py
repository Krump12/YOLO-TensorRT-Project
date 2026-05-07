from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.utils.config import load_config
from src.utils.logging import ErrorCategory, format_error
from src.web.app import create_app


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run YOLO TensorRT Web detection dashboard")
    parser.add_argument("--config", default="configs/jetson_orin_nano.yaml")
    parser.add_argument("--host")
    parser.add_argument("--port", type=int)
    parser.add_argument("--no-pipeline", action="store_true", help="start Web routes without camera/detector pipeline")
    return parser


def apply_overrides(config, args):
    if args.host:
        config.web.host = args.host
    if args.port is not None:
        config.web.port = args.port
    config.validate()
    return config


def build_app(config_path: str = "configs/jetson_orin_nano.yaml", *, start_pipeline: bool = True):
    config = load_config(config_path)
    return create_app(config, start_pipeline=start_pipeline)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = apply_overrides(load_config(args.config), args)
        app = create_app(config, start_pipeline=not args.no_pipeline)
        import uvicorn

        uvicorn.run(app, host=config.web.host, port=config.web.port)
        return 0
    except Exception as exc:
        info = format_error(exc, ErrorCategory.CONFIG, "check Web configuration and required environment variables")
        print(str(info), file=sys.stderr)
        return info.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
