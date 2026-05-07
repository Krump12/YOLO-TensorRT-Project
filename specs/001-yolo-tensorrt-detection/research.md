# Research: YOLO TensorRT Real-Time Detection

## Decision: Use Ultralytics export for `.pt` to TensorRT `.engine`

**Rationale**: The repository already contains Ultralytics YOLO code with
TensorRT export support through `format="engine"`. Reusing this path preserves
YOLO metadata handling, reduces custom converter risk, and aligns with the
existing package tests around export and CUDA behavior.

**Alternatives considered**:

- Manual PyTorch -> ONNX -> TensorRT builder pipeline: More control, but higher
  maintenance burden and more duplicated export logic.
- ONNX Runtime TensorRT provider: Useful for cross-platform execution, but the
  user explicitly requires TensorRT engine deployment on Jetson.

## Decision: Prefer FP16 TensorRT when supported, fall back to FP32 with explicit warning

**Rationale**: FP16 is required as the priority path for real-time Jetson
deployment. TensorRT can report whether fast FP16 is available; the exporter and
runtime should surface the chosen precision so users know whether the target
performance path is active.

**Alternatives considered**:

- Force FP16 unconditionally: Fails unnecessarily on unsupported or incompatible
  environments.
- Support INT8 in v1: Could improve speed but requires calibration data and
  adds scope not requested for the first release.

## Decision: Capture CSI frames with OpenCV backed by a Jetson GStreamer pipeline

**Rationale**: CSI camera access on Jetson commonly depends on a GStreamer
pipeline, while OpenCV provides a simple display and frame interface. This
keeps camera handling isolated in `src/camera` and lets the runtime validate
1080P negotiation, frame availability, and shutdown.

**Alternatives considered**:

- Direct V4L2 access: Less suitable for common Jetson CSI camera pipelines.
- Full GStreamer application graph: More flexible, but unnecessary for a local
  single-camera visualization runtime.

## Decision: Use bounded threaded capture with latest-frame behavior

**Rationale**: The spec requires camera reading and inference to be decoupled
and low latency. A bounded queue or latest-frame buffer prevents inference
slowdowns from causing unbounded memory growth or stale display latency. When
the detector cannot keep up, stale frames should be dropped in favor of recent
frames.

**Alternatives considered**:

- Single-threaded capture and inference loop: Simpler, but a slow inference
  call blocks capture and display responsiveness.
- Unbounded queue: Preserves every frame but violates latency and memory
  stability requirements.

## Decision: Render overlays with OpenCV in the runtime display loop

**Rationale**: OpenCV drawing is sufficient for bounding boxes, labels,
confidence, FPS, and object count with minimal additional dependencies. It also
keeps display latency predictable and testable through synthetic frames.

**Alternatives considered**:

- Browser or desktop GUI: More UI flexibility but unnecessary overhead for a
  Jetson local display.
- GStreamer overlay plugins: Higher integration complexity and harder unit
  testing for label/object-count correctness.

## Decision: Validate performance with hardware tests plus lightweight unit tests

**Rationale**: TensorRT engine loading, CSI camera stability, and 1080P FPS must
be validated on Jetson hardware. Pure unit tests can still cover config parsing,
metrics math, result-to-overlay mapping, shutdown state, and error handling.

**Alternatives considered**:

- Only manual demos: Insufficient for regression prevention.
- Full hardware tests in default CI: Not practical when CI lacks Jetson, CSI
  camera, and TensorRT runtime.
