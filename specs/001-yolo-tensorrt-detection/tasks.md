---
description: "Task list for YOLO TensorRT real-time detection implementation"
---

# Tasks: YOLO TensorRT Real-Time Detection

**Input**: Design documents from `/specs/001-yolo-tensorrt-detection/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/runtime-contract.md, quickstart.md

**Tests**: Required by the feature specification. Write tests before implementation where practical.

**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the requested project layout, configuration skeletons, and test structure.

- [X] T001 Create runtime package directories in src/camera/, src/inference/, src/visualization/, src/utils/, scripts/, configs/, models/, tests/unit/, tests/integration/, and tests/hardware/
- [X] T002 [P] Add package initializers in src/camera/__init__.py, src/inference/__init__.py, src/visualization/__init__.py, and src/utils/__init__.py
- [X] T003 [P] Create default runtime configuration in configs/jetson_orin_nano.yaml
- [X] T004 [P] Create default class-name mapping template in configs/classes.yaml
- [X] T005 [P] Create pytest marker and hardware-test options in tests/conftest.py
- [X] T006 [P] Create models/README.md documenting expected best.pt and best.engine artifact placement

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared utilities and data structures required before any user story can be implemented.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T007 [P] Implement configuration dataclasses and YAML loading in src/utils/config.py
- [X] T008 [P] Implement structured error categories and user-facing messages in src/utils/logging.py
- [X] T009 [P] Implement runtime metric counters, FPS smoothing, and memory sampling helpers in src/utils/metrics.py
- [X] T010 [P] Implement signal and keyboard shutdown state handling in src/utils/shutdown.py
- [X] T011 [P] Define ModelArtifact, InferenceArtifact, CameraStream, FramePacket, DetectionResult, RuntimeMetrics, and AppConfig dataclasses in src/utils/config.py
- [X] T012 [P] Add unit tests for valid and invalid configuration loading in tests/unit/test_config.py
- [X] T013 [P] Add unit tests for FPS, object-count, and memory metric calculations in tests/unit/test_metrics.py
- [X] T014 [P] Add unit tests for shutdown state transitions in tests/unit/test_shutdown.py
- [X] T015 Run foundational unit tests with pytest tests/unit/test_config.py tests/unit/test_metrics.py tests/unit/test_shutdown.py

**Checkpoint**: Shared config, metrics, logging, and shutdown foundations are ready.

---

## Phase 3: User Story 1 - Convert and Load Custom Detection Model (Priority: P1)

**Goal**: Accept a custom YOLO `.pt` model, export a TensorRT `.engine`, and validate that the engine can be loaded before camera startup.

**Independent Test**: Place a valid model in models/best.pt, run the export flow, and confirm models/best.engine loads without starting the CSI camera.

### Tests for User Story 1

- [X] T016 [P] [US1] Add unit tests for model path validation and class-name fallback behavior in tests/unit/test_model_artifacts.py
- [X] T017 [P] [US1] Add unit tests for TensorRT export option selection including FP16 preference and FP32 fallback in tests/unit/test_yolo_exporter.py
- [X] T018 [P] [US1] Add integration test for export command argument parsing and missing-model failure in tests/integration/test_export_cli.py
- [X] T019 [P] [US1] Add Jetson hardware test for TensorRT engine load validation in tests/hardware/test_engine_load.py

### Implementation for User Story 1

- [X] T020 [P] [US1] Implement model artifact validation and class-name loading helpers in src/inference/yolo_exporter.py
- [X] T021 [US1] Implement Ultralytics `.pt` to TensorRT `.engine` export flow with FP16 preference in src/inference/yolo_exporter.py
- [X] T022 [P] [US1] Implement TensorRT engine existence, metadata, and load validation in src/inference/engine_loader.py
- [X] T023 [US1] Implement export CLI with config and override arguments in scripts/export_tensorrt.py
- [X] T024 [US1] Add clear export and engine-load error handling using src/utils/logging.py
- [X] T025 [US1] Verify export contract behavior against specs/001-yolo-tensorrt-detection/contracts/runtime-contract.md
- [X] T026 [US1] Run US1 tests with pytest tests/unit/test_model_artifacts.py tests/unit/test_yolo_exporter.py tests/integration/test_export_cli.py

**Checkpoint**: The model can be prepared and the generated TensorRT engine can be validated without opening the camera.

---

## Phase 4: User Story 2 - Run Real-Time Camera Detection (Priority: P1)

**Goal**: Open the CSI camera, decouple frame capture from inference, run live detection, and release resources on exit or errors.

**Independent Test**: Connect a CSI camera, start runtime with a loadable engine, and verify live frames are processed continuously with clean shutdown.

### Tests for User Story 2

- [X] T027 [P] [US2] Add unit tests for Jetson GStreamer pipeline generation in tests/unit/test_csi_camera.py
- [X] T028 [P] [US2] Add unit tests for bounded latest-frame queue behavior in tests/unit/test_frame_reader.py
- [X] T029 [P] [US2] Add unit tests for detector result normalization from backend outputs in tests/unit/test_tensorrt_detector.py
- [X] T030 [P] [US2] Add integration test with synthetic frames and fake detector in tests/integration/test_runtime_pipeline.py
- [X] T031 [P] [US2] Add Jetson hardware test for stable CSI camera frame reads in tests/hardware/test_csi_camera.py

### Implementation for User Story 2

- [X] T032 [P] [US2] Implement Jetson CSI GStreamer pipeline builder and camera open/read/release lifecycle in src/camera/csi_camera.py
- [X] T033 [P] [US2] Implement bounded threaded latest-frame reader in src/camera/frame_reader.py
- [X] T034 [P] [US2] Implement TensorRT detector wrapper and DetectionResult mapping in src/inference/tensorrt_detector.py
- [X] T035 [US2] Implement runtime orchestration for engine load, camera start, capture, inference, and shutdown in scripts/run_realtime_detection.py
- [X] T036 [US2] Add camera, inference, and shutdown error reporting paths in scripts/run_realtime_detection.py
- [X] T037 [US2] Verify runtime command contract behavior against specs/001-yolo-tensorrt-detection/contracts/runtime-contract.md
- [X] T038 [US2] Run US2 non-hardware tests with pytest tests/unit/test_csi_camera.py tests/unit/test_frame_reader.py tests/unit/test_tensorrt_detector.py tests/integration/test_runtime_pipeline.py

**Checkpoint**: Live detection pipeline can process camera frames with engine inference and shut down cleanly.

---

## Phase 5: User Story 3 - View Detection Overlay and Runtime Metrics (Priority: P2)

**Goal**: Show live video with boxes, labels, confidence, FPS, and per-frame object count while keeping the display readable and responsive.

**Independent Test**: Use synthetic or controlled frames and verify overlays match detections, metrics update, and zero-detection frames remain responsive.

### Tests for User Story 3

- [X] T039 [P] [US3] Add unit tests for bounding-box clipping, label text, confidence formatting, and unknown class IDs in tests/unit/test_overlay.py
- [X] T040 [P] [US3] Add unit tests for displayed object count matching rendered boxes in tests/unit/test_display_metrics.py
- [X] T041 [P] [US3] Add integration test for synthetic frame visualization without camera hardware in tests/integration/test_visualization_pipeline.py
- [X] T042 [P] [US3] Add Jetson hardware test for 1080P display overlay readability in tests/hardware/test_visualization_display.py

### Implementation for User Story 3

- [X] T043 [P] [US3] Implement detection box, class-name, and confidence drawing in src/visualization/overlay.py
- [X] T044 [P] [US3] Implement FPS and current-frame object-count overlay rendering in src/visualization/overlay.py
- [X] T045 [P] [US3] Implement OpenCV display lifecycle, exit-key handling, and display failure reporting in src/visualization/display.py
- [X] T046 [US3] Integrate overlay and display modules into scripts/run_realtime_detection.py
- [X] T047 [US3] Add no-detection frame behavior and zero object count rendering in src/visualization/overlay.py
- [X] T048 [US3] Verify display contract behavior against specs/001-yolo-tensorrt-detection/contracts/runtime-contract.md
- [X] T049 [US3] Run US3 non-hardware tests with pytest tests/unit/test_overlay.py tests/unit/test_display_metrics.py tests/integration/test_visualization_pipeline.py

**Checkpoint**: Runtime display presents detections and metrics accurately on every processed frame.

---

## Phase 6: User Story 4 - Sustain Low-Latency Runtime Operation (Priority: P2)

**Goal**: Maintain at least 20 FPS at 1080P under normal operating conditions, keep capture responsive, and avoid memory growth during continuous operation.

**Independent Test**: Run the system continuously on Jetson and verify FPS, latency, memory stability, and graceful shutdown.

### Tests for User Story 4

- [X] T050 [P] [US4] Add unit tests for stale-frame dropping and queue-size limits in tests/unit/test_frame_reader_performance.py
- [X] T051 [P] [US4] Add unit tests for performance budget evaluation and warning thresholds in tests/unit/test_performance_budget.py
- [X] T052 [P] [US4] Add integration test for slow fake detector not blocking latest-frame acquisition in tests/integration/test_low_latency_pipeline.py
- [X] T053 [P] [US4] Add Jetson hardware FPS validation for 1080P runtime in tests/hardware/test_realtime_fps.py
- [X] T054 [P] [US4] Add Jetson hardware 30-minute memory stability validation in tests/hardware/test_memory_stability.py
- [X] T055 [P] [US4] Add Jetson hardware shutdown timing validation in tests/hardware/test_shutdown_timing.py

### Implementation for User Story 4

- [X] T056 [P] [US4] Add runtime performance budget configuration fields in configs/jetson_orin_nano.yaml
- [X] T057 [P] [US4] Implement latency sampling and budget status reporting in src/utils/metrics.py
- [X] T058 [US4] Enforce bounded capture/inference coordination and stale-frame dropping in src/camera/frame_reader.py
- [X] T059 [US4] Add runtime warnings for FPS below target, camera stalls, and memory growth in scripts/run_realtime_detection.py
- [X] T060 [US4] Add optional performance summary output on normal exit in scripts/run_realtime_detection.py
- [X] T061 [US4] Run US4 non-hardware tests with pytest tests/unit/test_frame_reader_performance.py tests/unit/test_performance_budget.py tests/integration/test_low_latency_pipeline.py

**Checkpoint**: Runtime has measurable low-latency behavior and hardware validation coverage for FPS, memory, and shutdown.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Documentation, final verification, and project-level consistency.

- [X] T062 [P] Update quickstart usage notes in specs/001-yolo-tensorrt-detection/quickstart.md
- [X] T063 [P] Add implementation README for runtime commands in docs/jetson-yolo-tensorrt.md
- [X] T064 [P] Add example class-name configuration in configs/classes.yaml
- [X] T065 Run lint or formatting checks on src/, scripts/, and tests/
- [X] T066 Run non-hardware regression tests with pytest tests/unit tests/integration
- [ ] T067 Run Jetson validation tests with pytest tests/hardware --run-jetson
- [ ] T068 Verify quickstart end-to-end on Jetson using configs/jetson_orin_nano.yaml and models/best.pt

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **US1 (Phase 3)**: Depends on Foundational; required before US2 live detection.
- **US2 (Phase 4)**: Depends on Foundational and a loadable engine from US1.
- **US3 (Phase 5)**: Depends on Foundational; can use synthetic frames before US2, then integrates with US2 runtime.
- **US4 (Phase 6)**: Depends on US2 frame pipeline and US3 metrics/display integration.
- **Polish (Phase 7)**: Depends on desired user stories being complete.

### User Story Dependencies

- **US1**: Independent model preparation increment and MVP prerequisite.
- **US2**: Requires US1 for real TensorRT engine, but can test runtime orchestration with fake detector.
- **US3**: Can be developed independently with synthetic frames, then integrated into US2 runtime.
- **US4**: Requires US2 capture/inference pipeline and US3 metrics to validate performance.

### Within Each User Story

- Tests are written before implementation where practical.
- Model/config validation precedes export and runtime commands.
- Camera and detector modules precede runtime orchestration.
- Overlay and metric modules precede display integration.
- Hardware tests run on Jetson after non-hardware tests pass.

---

## Parallel Opportunities

- T002-T006 can run in parallel after T001.
- T007-T014 can run in parallel after setup.
- US1 tests T016-T019 can run in parallel; T020 and T022 can run in parallel before T021/T023.
- US2 tests T027-T031 can run in parallel; T032-T034 can run in parallel before T035.
- US3 tests T039-T042 can run in parallel; T043-T045 can run in parallel before T046.
- US4 tests T050-T055 can run in parallel; T056 and T057 can run in parallel before T058-T060.
- Documentation tasks T062-T064 can run in parallel with final validation after implementation is stable.

---

## Parallel Example: User Story 1

```bash
Task: "T016 [P] [US1] Add unit tests for model path validation and class-name fallback behavior in tests/unit/test_model_artifacts.py"
Task: "T017 [P] [US1] Add unit tests for TensorRT export option selection including FP16 preference and FP32 fallback in tests/unit/test_yolo_exporter.py"
Task: "T018 [P] [US1] Add integration test for export command argument parsing and missing-model failure in tests/integration/test_export_cli.py"
Task: "T019 [P] [US1] Add Jetson hardware test for TensorRT engine load validation in tests/hardware/test_engine_load.py"
```

## Parallel Example: User Story 2

```bash
Task: "T032 [P] [US2] Implement Jetson CSI GStreamer pipeline builder and camera open/read/release lifecycle in src/camera/csi_camera.py"
Task: "T033 [P] [US2] Implement bounded threaded latest-frame reader in src/camera/frame_reader.py"
Task: "T034 [P] [US2] Implement TensorRT detector wrapper and DetectionResult mapping in src/inference/tensorrt_detector.py"
```

## Parallel Example: User Story 3

```bash
Task: "T043 [P] [US3] Implement detection box, class-name, and confidence drawing in src/visualization/overlay.py"
Task: "T044 [P] [US3] Implement FPS and current-frame object-count overlay rendering in src/visualization/overlay.py"
Task: "T045 [P] [US3] Implement OpenCV display lifecycle, exit-key handling, and display failure reporting in src/visualization/display.py"
```

## Parallel Example: User Story 4

```bash
Task: "T050 [P] [US4] Add unit tests for stale-frame dropping and queue-size limits in tests/unit/test_frame_reader_performance.py"
Task: "T051 [P] [US4] Add unit tests for performance budget evaluation and warning thresholds in tests/unit/test_performance_budget.py"
Task: "T052 [P] [US4] Add integration test for slow fake detector not blocking latest-frame acquisition in tests/integration/test_low_latency_pipeline.py"
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1 and Phase 2.
2. Complete US1 to export and validate the TensorRT engine.
3. Complete the minimum US2 runtime path to open CSI camera, run detection, and exit cleanly.
4. Validate with US1 and US2 tests before polishing overlays and performance budgets.

### Incremental Delivery

1. US1 delivers model conversion and engine validation.
2. US2 delivers live camera inference.
3. US3 adds complete visualization and metrics.
4. US4 hardens the runtime for 20 FPS, low latency, memory stability, and shutdown timing.

### Validation Gates

- Non-hardware unit/integration tests pass before Jetson hardware tests.
- Jetson hardware tests validate engine load, CSI camera, FPS, overlays, memory stability, and shutdown timing.
- Quickstart must execute end-to-end with `models/best.pt` and `configs/jetson_orin_nano.yaml`.
