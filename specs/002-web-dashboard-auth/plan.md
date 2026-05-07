# Implementation Plan: Web Dashboard Authentication

**Branch**: `feature/web` | **Date**: 2026-05-07 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/002-web-dashboard-auth/spec.md`

## Summary

Add a login-protected Web dashboard to the existing YOLO TensorRT CSI camera
detection runtime. The implementation will add a small FastAPI-based Web module
under `src/web/`, reuse the existing `LatestFrameReader`, `TensorRTDetector`,
overlay rendering, metrics, and configuration loader, and expose browser pages
for login, live annotated video, latest detection results, and runtime status.
The Web pipeline keeps one shared camera/detector workflow and publishes only
latest-frame state to bounded, thread-safe buffers for low latency.

## Technical Context

**Language/Version**: Python 3.8+ in JetPack-compatible environment  
**Primary Dependencies**: Existing TensorRT/CUDA/OpenCV/NumPy/PyYAML stack plus FastAPI, Uvicorn, Starlette sessions/templates, python-multipart for form login, and pytest TestClient support  
**Storage**: Local configuration and environment variables only; no database; no persisted detection history  
**Testing**: pytest unit/integration tests with mocked camera, detector, and shared buffers; Jetson hardware tests marked separately with existing `--run-jetson` flow  
**Target Platform**: NVIDIA Jetson Orin Nano running Ubuntu + JetPack with CSI camera; browser clients on local network
**Project Type**: Single Python edge-runtime application with a Web service module and static/template frontend  
**Performance Goals**: 1080P camera input; at least 20 browser-displayed FPS under normal target-device operation; latest detection table updates within 1 second for 95% of normal updates; shutdown releases resources within 3 seconds; one dashboard client causes no more than 10% FPS reduction versus non-Web runtime  
**Constraints**: Do not rewrite or duplicate the existing YOLO/TensorRT pipeline; do not open the CSI camera twice; prefer TensorRT FP16 through existing inference config; browser clients must not create unbounded frame queues; secrets must come from environment variables; existing CLI scripts remain behaviorally unchanged  
**Scale/Scope**: One Jetson device, one CSI camera, one active detector pipeline, one configured operator account for v1, a small number of local browser clients, latest-frame result display only

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: PASS. The plan adds a contained `src/web/` module and
  startup script while preserving existing `src/camera`, `src/inference`,
  `src/visualization`, and `src/utils` ownership. Shared latest-state classes
  are the smallest sufficient abstraction needed to separate Web delivery from
  camera/inference work.
- **Testing**: PASS. Required tests cover authentication success/failure,
  protected route access, JSON result/status contracts, schema serialization,
  and Web pipeline behavior with mocked camera/detector. Real CSI/TensorRT
  validation remains in hardware-marked tests.
- **UX Consistency**: PASS. Pages define login error/success, dashboard loading
  and non-ready states, detections empty state, status refresh behavior, logout,
  and responsive desktop layouts without overlapping controls.
- **Performance**: PASS. Budgets are explicit: 20 displayed FPS, latest result
  freshness within 1 second, bounded latest-frame buffers, no duplicate CSI
  camera open, <=10% FPS drop with one browser client, and 30-minute memory
  stability validation.
- **Maintainability**: PASS. Startup fails fast for missing secrets, runtime
  status exposes camera/detector readiness, shutdown stops the background
  pipeline, and configuration remains observable through the existing YAML plus
  environment variable pattern.

## Project Structure

### Documentation (this feature)

```text
specs/002-web-dashboard-auth/
|-- plan.md
|-- research.md
|-- data-model.md
|-- quickstart.md
|-- contracts/
|   `-- web-api.openapi.yaml
`-- tasks.md
```

### Source Code (repository root)

```text
configs/
|-- jetson_orin_nano.yaml

docs/
|-- web-dashboard.md

scripts/
|-- export_tensorrt.py
|-- run_realtime_detection.py
`-- run_web_detection.py

src/
|-- camera/
|-- inference/
|-- utils/
|-- visualization/
`-- web/
    |-- __init__.py
    |-- app.py
    |-- auth.py
    |-- routes.py
    |-- schemas.py
    |-- stream.py
    |-- static/
    |   |-- app.js
    |   `-- style.css
    `-- templates/
        |-- dashboard.html
        |-- detections.html
        `-- login.html

tests/
|-- test_web_auth.py
|-- test_web_routes.py
|-- test_detection_result_schema.py
|-- integration/
|   `-- test_web_pipeline.py
`-- hardware/
    `-- test_web_dashboard_runtime.py
```

**Structure Decision**: Use the existing single Python project layout. The Web
module lives under `src/web/` so it can import existing runtime packages without
creating a second backend/frontend project. Static HTML/CSS/JS stays colocated
with the Web routes because v1 does not need a separate frontend build system.
Existing CLI scripts remain in place and `scripts/run_web_detection.py` becomes
the only new Web entry point.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are captured in [research.md](research.md). Key outcomes:

- Use FastAPI/Starlette for the Web backend because it provides route tests,
  template rendering, streaming responses, and session middleware with minimal
  new code.
- Use MJPEG for v1 video delivery because it works with plain browser `<img>`
  tags and keeps the frontend simple; status and detections use JSON polling at
  a short interval to avoid adding a WebSocket dependency for latest-frame data.
- Reuse the existing `LatestFrameReader`, `TensorRTDetector`, `draw_overlay`,
  and `FpsCounter` in a single background detection pipeline.
- Publish annotated JPEG bytes and structured detection snapshots through a
  lock-protected latest-state buffer, never through unbounded per-client queues.
- Store username in YAML and read password/session secret from environment
  variables, failing startup when required secrets are missing.

## Phase 1: Design Summary

Design artifacts are captured in:

- [data-model.md](data-model.md)
- [contracts/web-api.openapi.yaml](contracts/web-api.openapi.yaml)
- [quickstart.md](quickstart.md)

Post-design Constitution Check: PASS. The design keeps the Web module scoped,
documents authenticated routes and JSON contracts, defines bounded shared state
for performance, and includes automated plus hardware validation paths. No
complexity exceptions were introduced.
