# Implementation Plan: YOLO TensorRT Real-Time Detection

**Branch**: `001-yolo-tensorrt-detection` | **Date**: 2026-05-06 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/001-yolo-tensorrt-detection/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Build a Python edge-AI runtime for NVIDIA Jetson Orin Nano that converts a user
YOLO `.pt` model into a TensorRT `.engine`, loads the engine for FP16-priority
inference, reads 1080P CSI camera frames through GStreamer, decouples capture
from inference with a bounded threaded frame pipeline, and displays real-time
OpenCV visualization with boxes, class names, confidence, FPS, and per-frame
object count.

## Technical Context

**Language/Version**: Python 3.8+ in JetPack-compatible environment  
**Primary Dependencies**: PyTorch, Ultralytics YOLO package in this repository, TensorRT, CUDA, cuDNN, OpenCV with GStreamer support, NumPy, PyYAML, psutil for runtime memory checks  
**Storage**: Local filesystem only; `.pt` and `.engine` artifacts in `models/`, configuration in `configs/`, no database  
**Testing**: pytest for unit/integration tests; Jetson hardware validation for TensorRT engine load, CSI camera read stability, 1080P visualization, FPS, shutdown, and memory stability  
**Target Platform**: NVIDIA Jetson Orin Nano running Ubuntu + JetPack with CSI camera  
**Project Type**: Single Python edge-runtime application with CLI entry points and modular source packages  
**Performance Goals**: At least 20 displayed FPS at 1080P under normal operating conditions; first annotated frame within 10 seconds; exit within 2 seconds; 30-minute run without unbounded memory growth  
**Constraints**: Prefer TensorRT FP16 when supported; capture and inference must be decoupled; bounded queues prevent latency buildup; all camera/display/TensorRT resources released on exit or error; runtime does not require network access after setup  
**Scale/Scope**: One local device, one CSI camera stream, one active detection model/engine at a time, real-time local display only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: PASS. Design uses explicit modules for camera, inference,
  visualization, metrics, config, and scripts. The runtime stays small and
  avoids new framework layers beyond the requested edge stack.
- **Testing**: PASS. Plan requires unit tests for config/metrics/result handling,
  integration tests for engine loading and camera frame flow, and hardware
  validation for FPS, overlays, shutdown, and memory stability.
- **UX Consistency**: PASS. Runtime display states cover startup readiness,
  camera/model errors, no-detection frames, live metrics, and real-time exit.
  Overlay placement is constrained to avoid obscuring the main camera view.
- **Performance**: PASS. Budgets are explicit: 1080P input, at least 20 FPS,
  first annotated frame within 10 seconds, exit within 2 seconds, bounded
  queueing, and 30-minute memory stability validation.
- **Maintainability**: PASS. Failure modes are explicit at model conversion,
  engine loading, camera setup, frame read, inference, visualization, and
  shutdown boundaries. No global runtime state is required outside config and
  lifecycle objects.

## Project Structure

### Documentation (this feature)

```text
specs/001-yolo-tensorrt-detection/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- runtime-contract.md
`-- tasks.md
```

### Source Code (repository root)

```text
configs/
|-- jetson_orin_nano.yaml
`-- classes.yaml

models/
|-- best.pt
`-- best.engine

scripts/
|-- export_tensorrt.py
`-- run_realtime_detection.py

src/
|-- camera/
|   |-- __init__.py
|   |-- csi_camera.py
|   `-- frame_reader.py
|-- inference/
|   |-- __init__.py
|   |-- engine_loader.py
|   |-- tensorrt_detector.py
|   `-- yolo_exporter.py
|-- visualization/
|   |-- __init__.py
|   |-- overlay.py
|   `-- display.py
`-- utils/
    |-- __init__.py
    |-- config.py
    |-- logging.py
    |-- metrics.py
    `-- shutdown.py

tests/
|-- unit/
|-- integration/
`-- hardware/
```

**Structure Decision**: Use a single Python project rooted at the repository
root. Keep user model artifacts under `models/`, command scripts under
`scripts/`, runtime modules under `src/`, configuration under `configs/`, and
feature-specific tests grouped by unit, integration, and Jetson hardware
validation. This matches the user-specified engineering layout while leaving
the existing `ultralytics/` package untouched except as a dependency/source of
export behavior.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are captured in [research.md](research.md). Key outcomes:

- Use Ultralytics export path for `.pt` to TensorRT `.engine` to reuse existing
  repository behavior and metadata handling.
- Use OpenCV `VideoCapture` with a Jetson GStreamer pipeline for CSI input.
- Use a bounded producer/consumer frame queue to decouple capture and inference
  while dropping stale frames instead of growing latency.
- Use OpenCV overlay rendering for low-overhead visualization.
- Use pytest plus Jetson-only hardware tests for behavior that cannot be
  validated on non-Jetson development machines.

## Phase 1: Design Summary

Design artifacts are captured in:

- [data-model.md](data-model.md)
- [contracts/runtime-contract.md](contracts/runtime-contract.md)
- [quickstart.md](quickstart.md)

Post-design Constitution Check: PASS. The design artifacts preserve the same
module boundaries, test strategy, UX states, and performance validation methods
defined above. No new complexity exceptions were introduced.
