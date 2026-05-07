# Data Model: YOLO TensorRT Real-Time Detection

## ModelArtifact

**Purpose**: Represents the user-provided YOLO `.pt` model.

**Fields**:

- `path`: Filesystem path to the `.pt` model.
- `exists`: Whether the model file is present and readable.
- `input_size`: Expected inference image size, default from configuration.
- `class_names`: Ordered class-name mapping used for visualization.
- `source_format`: Always `pt` for v1.

**Validation Rules**:

- Path must exist and end with `.pt`.
- Class names must be available from model metadata or `configs/classes.yaml`.
- Input size must be positive and supported by the model/export path.

## InferenceArtifact

**Purpose**: Represents the TensorRT `.engine` generated from the model.

**Fields**:

- `path`: Filesystem path to the `.engine` file.
- `precision`: `fp16` when supported and requested, otherwise `fp32`.
- `source_model_path`: ModelArtifact path used to create the engine.
- `device`: Target Jetson/GPU device identifier.
- `load_status`: `missing`, `exported`, `loaded`, or `failed`.

**Validation Rules**:

- Engine path must end with `.engine`.
- Engine must be loadable before live detection starts.
- Precision selection must be logged and visible in startup status.

**State Transitions**:

`missing` -> `exported` -> `loaded`  
`missing` -> `failed`  
`exported` -> `failed`

## CameraStream

**Purpose**: Represents the live CSI camera source and negotiated stream state.

**Fields**:

- `pipeline`: GStreamer pipeline string or generated pipeline config.
- `width`: Requested width, default `1920`.
- `height`: Requested height, default `1080`.
- `fps`: Requested camera FPS.
- `connected`: Whether the camera opened successfully.
- `last_frame_time`: Timestamp of the latest acquired frame.
- `dropped_frames`: Count of skipped/stale frames.

**Validation Rules**:

- Requested width and height must be positive.
- Runtime must fail clearly if the camera cannot open.
- Runtime must report when requested 1080P cannot be negotiated.

## FramePacket

**Purpose**: Carries a camera frame through the runtime pipeline.

**Fields**:

- `frame_id`: Monotonic frame identifier.
- `timestamp`: Acquisition timestamp.
- `image`: Frame pixels.
- `source_width`: Frame width.
- `source_height`: Frame height.

**Validation Rules**:

- Frame image must be non-empty.
- Frame IDs must increase monotonically during a session.

## DetectionResult

**Purpose**: Represents one detected object in a frame.

**Fields**:

- `frame_id`: FramePacket identifier.
- `bbox`: `x1`, `y1`, `x2`, `y2` coordinates in display-frame pixels.
- `class_id`: Numeric class identifier.
- `class_name`: Human-readable label.
- `confidence`: Floating-point confidence score from 0.0 to 1.0.

**Validation Rules**:

- Bounding box coordinates must be inside or clipped to the displayed frame.
- Confidence must be between 0.0 and 1.0.
- Class IDs must map to configured class names; unknown IDs render as
  `unknown:<id>`.

## RuntimeMetrics

**Purpose**: Tracks performance and live-display measurements.

**Fields**:

- `fps`: Displayed frames per second.
- `object_count`: Number of rendered detections for the current frame.
- `capture_latency_ms`: Time from camera acquisition to pipeline availability.
- `inference_latency_ms`: Time spent in detector execution.
- `display_latency_ms`: Time spent rendering and showing the frame.
- `memory_mb`: Runtime memory sample.
- `started_at`: Session start timestamp.

**Validation Rules**:

- Object count must equal the number of rendered detection boxes.
- FPS must update continuously during live operation.
- Memory samples during 30-minute validation must not show unbounded growth.

## AppConfig

**Purpose**: Holds user-adjustable runtime settings.

**Fields**:

- `model_path`: Path to `.pt` file.
- `engine_path`: Path to `.engine` file.
- `classes_path`: Path to class names file.
- `camera`: Width, height, FPS, sensor ID, and flip method.
- `inference`: Image size, confidence threshold, IoU threshold, precision, and
  max detections.
- `runtime`: Queue size, display window name, exit key, logging level, and
  performance validation duration.

**Validation Rules**:

- Required paths must be present or creatable.
- Confidence and IoU thresholds must be between 0.0 and 1.0.
- Queue size must be bounded and at least 1.
