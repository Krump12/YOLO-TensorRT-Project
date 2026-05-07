# Tasks: Web Dashboard Authentication

**Input**: Design documents from `/specs/002-web-dashboard-auth/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/
**Tests**: Automated tests are required by the specification for authentication, protected routes, schemas, status, latest detections, and mocked Web pipeline behavior.
**Organization**: Tasks are grouped by user story so each story can be implemented and tested independently after shared foundation is complete.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it touches different files and has no dependency on incomplete tasks in the same phase
- **[Story]**: User story label, only used in user story phases
- Every task includes an exact file path

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the Web module skeleton, configuration placeholders, and project documentation entry points.

- [X] T001 Create Web package directories and placeholder files in src/web/__init__.py, src/web/app.py, src/web/auth.py, src/web/routes.py, src/web/schemas.py, and src/web/stream.py
- [X] T002 [P] Create frontend asset directories and placeholder files in src/web/templates/login.html, src/web/templates/dashboard.html, src/web/templates/detections.html, src/web/static/style.css, and src/web/static/app.js
- [X] T003 [P] Create Web startup script placeholder in scripts/run_web_detection.py
- [X] T004 [P] Create Web usage documentation placeholder in docs/web-dashboard.md
- [X] T005 [P] Create environment variable example file in .env.example
- [X] T006 Add FastAPI/Uvicorn/python-multipart dependency notes to docs/web-dashboard.md because the repository has no dependency manifest file

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared configuration, schemas, app construction, and pipeline state that all user stories depend on.

**Critical**: No user story work can begin until this phase is complete.

- [X] T007 Extend AppConfig with WebConfig parsing and validation in src/utils/config.py
- [X] T008 Extend configs/jetson_orin_nano.yaml with web host, port, username, password_env, stream_fps, jpeg_quality, and session_secret_env settings
- [X] T009 [P] Add unit tests for WebConfig defaults, validation, and missing environment secret behavior in tests/unit/test_config.py
- [X] T010 [P] Implement BoundingBoxDTO, DetectionDTO, DetectionSnapshotDTO, RuntimeStatusDTO, and serialization helpers in src/web/schemas.py
- [X] T011 [P] Add schema tests for class_name, confidence, bbox, timestamp, fps, target_count, and empty detections in tests/test_detection_result_schema.py
- [X] T012 Implement lock-protected latest frame/result/status buffer primitives in src/web/stream.py
- [X] T013 Add mocked latest-state buffer tests for overwrite behavior and no unbounded queue growth in tests/integration/test_web_pipeline.py
- [X] T014 Implement FastAPI app factory with static/template mounting and session middleware wiring in src/web/app.py
- [X] T015 Implement shared route dependency hooks for app config, latest-state buffer, and authentication checks in src/web/routes.py
- [X] T016 Implement run_web_detection.py argument parsing and config loading without starting camera work in scripts/run_web_detection.py

**Checkpoint**: Foundation ready; user story implementation can now begin.

---

## Phase 3: User Story 1 - Secure Access to Detection System (Priority: P1) MVP

**Goal**: Operators can log in, reach protected pages, log out, and unauthenticated users cannot access protected pages or data feeds.

**Independent Test**: With mocked app state and configured test credentials, route tests verify root redirects, successful login, failed login, logout, and denial of protected pages/endpoints before login.

### Tests for User Story 1

- [X] T017 [P] [US1] Add authentication success, bad password, and logout tests in tests/test_web_auth.py
- [X] T018 [P] [US1] Add unauthenticated protection tests for /dashboard, /detections, /video_feed, /api/detections/latest, and /api/status in tests/test_web_routes.py
- [X] T019 [P] [US1] Add authenticated dashboard access test in tests/test_web_routes.py

### Implementation for User Story 1

- [X] T020 [US1] Implement server-side credential loading, constant-time password verification, login session creation, and logout session clearing in src/web/auth.py
- [X] T021 [US1] Implement GET /, GET /login, POST /login, POST /logout, and authentication redirect behavior in src/web/routes.py
- [X] T022 [US1] Implement login page form, error state, and no frontend password exposure in src/web/templates/login.html
- [X] T023 [US1] Add protected-page navigation and logout form shell in src/web/templates/dashboard.html and src/web/templates/detections.html
- [X] T024 [US1] Add basic responsive authentication and navigation styling in src/web/static/style.css
- [X] T025 [US1] Wire app factory routes and session middleware into scripts/run_web_detection.py for a login-only runnable Web service

**Checkpoint**: User Story 1 is functional and independently testable as the MVP.

---

## Phase 4: User Story 2 - Monitor Live Detection Video (Priority: P2)

**Goal**: Authenticated operators can view a live annotated camera stream with FPS and target count while reusing the existing detection pipeline exactly once.

**Independent Test**: With mocked camera and detector, dashboard tests verify MJPEG output uses shared annotated frames, status returns FPS/target count, and pipeline lifecycle does not open duplicate camera resources.

### Tests for User Story 2

- [X] T026 [P] [US2] Add authenticated /video_feed MJPEG response test using mocked latest frame bytes in tests/test_web_routes.py
- [X] T027 [P] [US2] Add /api/status JSON contract test for camera_running, detector_loaded, fps, and target_count in tests/test_web_routes.py
- [X] T028 [P] [US2] Add mocked Web pipeline test that reuses LatestFrameReader, TensorRTDetector, draw_overlay, and FpsCounter in tests/integration/test_web_pipeline.py
- [X] T029 [P] [US2] Add Jetson hardware test scaffold for Web dashboard FPS, single CSI camera ownership, and shutdown timing in tests/hardware/test_web_dashboard_runtime.py

### Implementation for User Story 2

- [X] T030 [US2] Implement WebDetectionPipeline lifecycle with CSICamera, LatestFrameReader, TensorRTDetector, draw_overlay, FpsCounter, and graceful stop in src/web/stream.py
- [X] T031 [US2] Implement JPEG encoding with configurable jpeg_quality and stream_fps throttling in src/web/stream.py
- [X] T032 [US2] Implement GET /dashboard, GET /video_feed, and GET /api/status handlers in src/web/routes.py
- [X] T033 [US2] Implement dashboard video, FPS, target count, loading state, and non-ready state markup in src/web/templates/dashboard.html
- [X] T034 [US2] Implement status polling and dashboard metric updates in src/web/static/app.js
- [X] T035 [US2] Add dashboard responsive layout and low-latency visual styling in src/web/static/style.css
- [X] T036 [US2] Start and stop WebDetectionPipeline from FastAPI lifespan in src/web/app.py
- [X] T037 [US2] Wire uvicorn startup with host and port settings in scripts/run_web_detection.py

**Checkpoint**: User Stories 1 and 2 work independently after shared foundation.

---

## Phase 5: User Story 3 - Review Current Detection Results (Priority: P3)

**Goal**: Authenticated operators can view the latest-frame detection table, including empty state and automatic refresh.

**Independent Test**: With mocked latest detection snapshots, route and frontend tests verify required JSON fields, latest-frame strategy text, table updates, and empty state behavior.

### Tests for User Story 3

- [X] T038 [P] [US3] Add authenticated /api/detections/latest JSON structure test with timestamp, fps, target_count, class_name, confidence, and bbox in tests/test_web_routes.py
- [X] T039 [P] [US3] Add detections page access and empty state rendering test in tests/test_web_routes.py
- [X] T040 [P] [US3] Add schema conversion test from src.utils.config.DetectionResult to DetectionSnapshotDTO in tests/test_detection_result_schema.py

### Implementation for User Story 3

- [X] T041 [US3] Implement latest detection snapshot conversion from DetectionResult objects in src/web/schemas.py
- [X] T042 [US3] Implement GET /detections and GET /api/detections/latest handlers in src/web/routes.py
- [X] T043 [US3] Implement latest-frame strategy label, detection table, and no-target empty state in src/web/templates/detections.html
- [X] T044 [US3] Implement detections polling, table rendering, timestamp display, and empty state switching in src/web/static/app.js
- [X] T045 [US3] Add detections table responsive styling and confidence formatting styles in src/web/static/style.css

**Checkpoint**: All user stories are independently functional.

---

## Phase 6: Polish & Cross-Cutting Concerns

**Purpose**: Finish documentation, compatibility checks, and validation across all stories.

- [X] T046 [P] Document branch creation, environment variables, startup command, Jetson IP discovery, and troubleshooting in docs/web-dashboard.md
- [X] T047 [P] Ensure .env.example documents YOLO_WEB_PASSWORD and YOLO_WEB_SESSION_SECRET without real secret values in .env.example
- [X] T048 [P] Add quickstart validation notes for default pytest and hardware pytest commands in docs/web-dashboard.md
- [X] T049 Run default Web tests and record command coverage in docs/web-dashboard.md
- [X] T050 Run existing non-Web unit/integration tests that cover scripts/run_realtime_detection.py compatibility and fix any regressions in affected files
- [ ] T051 Run manual or hardware-marked performance validation for 20 FPS, <=10% Web overhead, 30-minute memory stability, and graceful shutdown using tests/hardware/test_web_dashboard_runtime.py
- [X] T052 Review UI states for login, dashboard, detections, loading, empty, error, and logout flows in src/web/templates/login.html, src/web/templates/dashboard.html, src/web/templates/detections.html, src/web/static/style.css, and src/web/static/app.js

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; recommended MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational and uses US1 authentication for protected access.
- **User Story 3 (Phase 5)**: Depends on Foundational and uses US1 authentication for protected access.
- **Polish (Phase 6)**: Depends on the selected user stories being complete.

### User Story Dependencies

- **US1 Secure Access**: No other user story dependency after Foundational.
- **US2 Live Video Dashboard**: Requires the auth guard from US1 for production behavior, but its pipeline/status work can be developed against mocked authenticated clients after Foundational.
- **US3 Detection Results Page**: Requires the auth guard from US1 for production behavior, but its schema/API/table work can be developed against mocked authenticated clients after Foundational.

### Within Each User Story

- Write the story tests first and verify they fail where practical.
- Implement shared models/schemas before routes that serialize them.
- Implement services/pipeline lifecycle before endpoints that expose pipeline state.
- Implement route behavior before final template and JavaScript polish.
- Validate the checkpoint before moving to the next priority story.

### Parallel Opportunities

- Setup placeholders T002-T005 can run in parallel.
- Foundational tests T009, T011, and T013 can run in parallel with schema/app skeleton work after target files exist.
- US1 tests T017-T019 can run in parallel before implementation.
- US2 tests T026-T029 can run in parallel before pipeline implementation.
- US3 tests T038-T040 can run in parallel before detections implementation.
- Documentation tasks T046-T048 can run in parallel during polish.

---

## Parallel Example: User Story 1

```text
Task: "T017 [P] [US1] Add authentication success, bad password, and logout tests in tests/test_web_auth.py"
Task: "T018 [P] [US1] Add unauthenticated protection tests for protected pages and APIs in tests/test_web_routes.py"
Task: "T019 [P] [US1] Add authenticated dashboard access test in tests/test_web_routes.py"
```

## Parallel Example: User Story 2

```text
Task: "T026 [P] [US2] Add authenticated /video_feed MJPEG response test using mocked latest frame bytes in tests/test_web_routes.py"
Task: "T027 [P] [US2] Add /api/status JSON contract test in tests/test_web_routes.py"
Task: "T028 [P] [US2] Add mocked Web pipeline reuse test in tests/integration/test_web_pipeline.py"
Task: "T029 [P] [US2] Add Jetson hardware test scaffold in tests/hardware/test_web_dashboard_runtime.py"
```

## Parallel Example: User Story 3

```text
Task: "T038 [P] [US3] Add authenticated /api/detections/latest JSON structure test in tests/test_web_routes.py"
Task: "T039 [P] [US3] Add detections page access and empty state rendering test in tests/test_web_routes.py"
Task: "T040 [P] [US3] Add schema conversion test in tests/test_detection_result_schema.py"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1 setup.
2. Complete Phase 2 foundation.
3. Complete Phase 3 secure access.
4. Stop and validate login, logout, and protected route behavior independently.

### Incremental Delivery

1. Deliver secure access first so no live camera data is exposed.
2. Add the live video dashboard and status API using mocked pipeline tests first, then Jetson validation.
3. Add the detections table and latest JSON contract.
4. Finish docs, compatibility checks, and performance validation.

### Parallel Team Strategy

1. Complete Setup and Foundational phases together.
2. After foundation, one developer can finish US1 auth while another develops US2 pipeline/status tests and another develops US3 schema/table tests.
3. Integrate through the shared app factory and auth dependency before polish.

## Notes

- [P] tasks use different files or can be done before implementation without blocking each other.
- Story labels map directly to the prioritized user stories in spec.md.
- Avoid duplicating TensorRT inference or opening the CSI camera from Web routes.
- Preserve scripts/run_realtime_detection.py behavior while adding scripts/run_web_detection.py.
