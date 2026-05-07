# Jetson YOLO TensorRT Runtime

This runtime converts a custom YOLO `.pt` model to a TensorRT `.engine`, reads
CSI camera frames on Jetson through GStreamer, runs real-time detection, and
shows OpenCV overlays with boxes, labels, confidence, FPS, and object count.

## Commands

Export the engine:

```bash
python scripts/export_tensorrt.py --config configs/jetson_orin_nano.yaml
```

Run live detection:

```bash
python scripts/run_realtime_detection.py --config configs/jetson_orin_nano.yaml
```

Run without opening a display window for integration testing:

```bash
python scripts/run_realtime_detection.py --config configs/jetson_orin_nano.yaml --no-display
```

## Validation

Run non-hardware tests from any Python environment with the project
dependencies installed:

```bash
pytest tests/unit tests/integration
```

Run Jetson hardware validation on the target device:

```bash
pytest tests/hardware --run-jetson
```

The hardware pass validates TensorRT engine loading, CSI camera reads, 1080P
display behavior, FPS budget, memory stability, and shutdown timing.
