# Quickstart: YOLO TensorRT Real-Time Detection

## Prerequisites

- NVIDIA Jetson Orin Nano running Ubuntu + JetPack.
- CUDA, cuDNN, TensorRT, PyTorch, OpenCV with GStreamer support, and the local
  Ultralytics package available in the Python environment.
- CSI camera connected and visible to the Jetson camera stack.
- Custom YOLO `.pt` model available at `models/best.pt`.

## 1. Prepare Configuration

Create or edit `configs/jetson_orin_nano.yaml`:

```yaml
model:
  pt_path: models/best.pt
  engine_path: models/best.engine
  classes_path: configs/classes.yaml

camera:
  sensor_id: 0
  width: 1920
  height: 1080
  fps: 30
  flip_method: 0

inference:
  imgsz: 640
  precision: fp16
  conf_threshold: 0.25
  iou_threshold: 0.45
  max_detections: 300

runtime:
  queue_size: 2
  window_name: YOLO TensorRT Detection
  exit_key: q
  log_level: INFO
  memory_check_interval_sec: 5
```

## 2. Export TensorRT Engine

```bash
python scripts/export_tensorrt.py --config configs/jetson_orin_nano.yaml
```

Expected result:

- `models/best.engine` exists.
- Command reports selected precision, preferring FP16 when supported.
- Invalid model or TensorRT environment errors are reported clearly.

Use `--force` to rebuild an existing engine after changing the model,
precision, or image size.

## 3. Run Live Detection

```bash
python scripts/run_realtime_detection.py --config configs/jetson_orin_nano.yaml
```

Expected result:

- Engine loads before camera startup.
- 1080P CSI video appears in a display window.
- Detected objects show bounding boxes, class names, and confidence values.
- FPS and current frame object count update continuously.
- Press `q` or send interrupt to exit cleanly.

## 4. Validate Behavior

Run automated tests that do not require hardware:

```bash
pytest tests/unit tests/integration
```

Run Jetson hardware validation on the target device:

```bash
pytest tests/hardware --run-jetson
```

Hardware validation must cover:

- TensorRT engine loads correctly.
- CSI camera reads stable frames.
- Runtime sustains at least 20 FPS at 1080P under normal operating conditions.
- Detection boxes, class labels, confidence, FPS, and object count render
  correctly.
- Exit completes within 2 seconds and resources are released.
- 30-minute run does not show unbounded memory growth.

Hardware tests are marked `jetson` and are skipped unless `--run-jetson` is
provided. Run them only on the Jetson Orin Nano with the CSI camera connected.
