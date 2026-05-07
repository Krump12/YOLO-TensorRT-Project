# Runtime Contract: YOLO TensorRT Real-Time Detection

## CLI Commands

### Export Engine

```bash
python scripts/export_tensorrt.py --config configs/jetson_orin_nano.yaml
```

**Inputs**:

- `--config`: Path to runtime configuration.
- Optional overrides for `--model`, `--engine`, `--imgsz`, `--fp16`, and
  `--force`.

**Expected behavior**:

- Validates the source `.pt` model.
- Creates or replaces the `.engine` only when missing or `--force` is provided.
- Prints the selected precision and output engine path.
- Exits non-zero with a clear message for missing model, failed export, or
  unsupported target environment.

### Run Live Detection

```bash
python scripts/run_realtime_detection.py --config configs/jetson_orin_nano.yaml
```

**Inputs**:

- `--config`: Path to runtime configuration.
- Optional overrides for model/engine path, camera sensor ID, resolution,
  confidence threshold, and display enablement.

**Expected behavior**:

- Loads and validates the TensorRT engine before opening the camera.
- Opens the CSI camera at requested resolution when available.
- Displays live video with boxes, class names, confidence, FPS, and object
  count.
- Exits within 2 seconds after the configured exit key or interrupt.
- Releases camera, inference, and display resources on all exits.

## Configuration Schema

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

## Runtime Display Contract

Each displayed frame MUST include:

- Live camera image.
- One bounding box per rendered detection.
- Class name and confidence for each rendered detection.
- Current FPS.
- Current frame object count.

The object count MUST equal the number of rendered boxes. Metric overlays MUST
remain readable at 1080P and avoid covering more than the allowed overlay area
outside object regions.

## Error Contract

All user-facing failures MUST include:

- Error category: model, export, engine, camera, inference, display, config, or
  shutdown.
- Short human-readable message.
- Recommended next check, such as missing file path, camera connection, or
  environment support.
- Non-zero exit code for command failures.
