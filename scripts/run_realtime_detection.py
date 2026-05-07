from __future__ import annotations

import argparse
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.camera.csi_camera import CSICamera
from src.camera.frame_reader import LatestFrameReader
from src.inference.tensorrt_detector import TensorRTDetector
from src.utils.config import load_class_names, load_config
from src.utils.logging import ErrorCategory, format_error
from src.utils.metrics import FpsCounter, PerformanceBudget, current_memory_mb
from src.utils.shutdown import ShutdownController


def frame_signature(frame) -> float:
    try:
        return float(frame[::32, ::32].mean())
    except Exception:
        return 0.0


def format_detection_debug(detections, limit: int = 3) -> str:
    parts = []
    for detection in list(detections)[:limit]:
        parts.append(
            f"{detection.class_name}:{detection.confidence:.2f}@"
            f"{detection.bbox[0]},{detection.bbox[1]},{detection.bbox[2]},{detection.bbox[3]}"
        )
    return " | ".join(parts) if parts else "-"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run real-time YOLO TensorRT detection")
    parser.add_argument("--config", default="configs/jetson_orin_nano.yaml")
    parser.add_argument("--engine")
    parser.add_argument("--sensor-id", type=int)
    parser.add_argument("--width", type=int)
    parser.add_argument("--height", type=int)
    parser.add_argument("--conf", type=float)
    parser.add_argument("--no-display", action="store_true")
    parser.add_argument("--debug-detections", action="store_true", help="print per-frame detection counts")
    parser.add_argument("--debug-save-dir", help="save raw camera frames for offline model comparison")
    parser.add_argument("--debug-save-limit", type=int, default=10, help="maximum raw frames to save with --debug-save-dir")
    return parser


def apply_overrides(config, args):
    if args.engine:
        config.engine_path = Path(args.engine)
    if args.sensor_id is not None:
        config.camera.sensor_id = args.sensor_id
    if args.width:
        config.camera.width = args.width
    if args.height:
        config.camera.height = args.height
    if args.conf is not None:
        config.conf_threshold = args.conf
    config.validate()
    return config


def run_pipeline(
    config,
    detector=None,
    camera=None,
    display=None,
    max_frames: int | None = None,
    debug_detections: bool = False,
    debug_save_dir: str | Path | None = None,
    debug_save_limit: int = 10,
) -> int:
    shutdown = ShutdownController()
    fps = FpsCounter()
    memory_start = current_memory_mb()
    budget = PerformanceBudget(config.target_fps, config.memory_growth_mb_limit)
    class_names = load_class_names(config.classes_path)
    detector = detector or TensorRTDetector(
        config.engine_path,
        class_names,
        imgsz=config.imgsz,
        conf=config.conf_threshold,
        iou=config.iou_threshold,
        max_det=config.max_detections,
    ).load()
    camera = camera or CSICamera(config.camera).open()
    reader = LatestFrameReader(camera, queue_size=config.queue_size)
    reader.start()
    processed = 0
    previous_signature: float | None = None
    saved_debug_frames = 0
    debug_save_path = Path(debug_save_dir) if debug_save_dir else None
    if debug_save_path is not None:
        debug_save_path.mkdir(parents=True, exist_ok=True)
    try:
        while not shutdown.requested:
            packet = reader.read_latest(timeout=1.0)
            if packet is None:
                continue
            if debug_save_path is not None and saved_debug_frames < debug_save_limit:
                try:
                    import cv2

                    raw_path = debug_save_path / f"frame_{packet.frame_id:06d}.jpg"
                    cv2.imwrite(str(raw_path), packet.image)
                    saved_debug_frames += 1
                    print(f"[debug-frame] saved {raw_path}")
                except Exception as exc:
                    print(f"[debug-frame] save failed: {exc}", file=sys.stderr)
                    debug_save_path = None
            detections = detector.detect(packet.frame_id, packet.image)
            if debug_detections:
                signature = frame_signature(packet.image)
                delta = 0.0 if previous_signature is None else abs(signature - previous_signature)
                previous_signature = signature
                print(
                    f"[detections] frame={packet.frame_id} count={len(detections)} "
                    f"frame_mean={signature:.2f} frame_delta={delta:.2f} "
                    f"boxes={format_detection_debug(detections)}"
                )
            current_fps = fps.tick()
            warnings = budget.evaluate(current_fps, memory_start, current_memory_mb())
            for warning in warnings:
                print(f"[performance] {warning}", file=sys.stderr)
            if display is not None:
                key = display.show(packet.image, detections, current_fps)
                shutdown.check_key(key, config.exit_key)
            processed += 1
            if max_frames is not None and processed >= max_frames:
                break
        return 0
    finally:
        started = time.perf_counter()
        reader.stop()
        if display is not None:
            display.close()
        print(f"Performance summary: frames={processed}, dropped={reader.dropped_frames}")
        if time.perf_counter() - started > config.max_exit_seconds:
            print("[shutdown] resource release exceeded exit budget", file=sys.stderr)


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        config = apply_overrides(load_config(args.config), args)
        display = None
        if not args.no_display:
            from src.visualization.display import OpenCVDisplay

            display = OpenCVDisplay(config.window_name, config.exit_key)
        return run_pipeline(
            config,
            display=display,
            debug_detections=args.debug_detections,
            debug_save_dir=args.debug_save_dir,
            debug_save_limit=args.debug_save_limit,
        )
    except Exception as exc:
        info = format_error(exc, ErrorCategory.INFERENCE, "check model engine, camera, and display configuration")
        print(str(info), file=sys.stderr)
        return info.exit_code


if __name__ == "__main__":
    raise SystemExit(main())
