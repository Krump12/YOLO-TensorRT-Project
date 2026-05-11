# Tasks: Agent Detection Dashboard

**Input**: Design documents from `/specs/003-agent-detection-dashboard/`
**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Automated tests are REQUIRED for changed behavior. Include the lowest useful test level and add integration, contract, or end-to-end coverage for user-visible workflows or cross-module contracts.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (US1, US2, US3, US4)
- Include exact file paths in descriptions

## Path Conventions

- Single Python edge-runtime project
- Source code lives under `src/`
- Web templates and static assets live under `src/web/templates/` and `src/web/static/`
- Tests live under `tests/`, `tests/integration/`, and `tests/hardware/`

---

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Prepare shared project configuration, documentation, and test fixtures for the revised feature scope.

- [X] T001 Add Web persistence and Agent configuration defaults to `configs/jetson_orin_nano.yaml`
- [X] T002 [P] Add Web persistence and Agent environment examples to `.env.example`
- [X] T003 [P] Add shared Web feature test fixtures for storage path, authenticated client, mocked clock, and mocked Agent provider in `tests/conftest.py`
- [X] T004 [P] Add OpenAPI contract fixture loader for `specs/003-agent-detection-dashboard/contracts/web-api.openapi.yaml` in `tests/conftest.py`
- [X] T005 [P] Update dashboard documentation outline for detection history, Agent analysis, Agent Q&A, and i18n in `docs/web-dashboard.md`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Shared infrastructure that MUST be complete before any user story can be implemented.

**CRITICAL**: No user story work can begin until this phase is complete.

- [X] T006 Create SQLite connection, schema initialization, and migration guard helpers in `src/web/storage.py`
- [X] T007 Define DetectionRecord, AgentAnalysisResult, AgentChatMessage, language, and shared response DTOs in `src/web/schemas.py`
- [X] T008 Add storage, Agent service, chat service, and i18n dependency initialization to app state in `src/web/app.py`
- [X] T009 Add authenticated API dependency helpers and shared error response helpers in `src/web/routes.py`
- [X] T010 [P] Add base navigation entries for dashboard, detection history, Agent analysis, Agent chat, and language switching in `src/web/templates/dashboard.html`
- [X] T011 [P] Add shared frontend API helper, language state helper, and rendering utility structure in `src/web/static/app.js`
- [X] T012 [P] Add shared CSS states for loading, empty, error, disabled, success, filters, detail panels, analysis cards, and chat messages in `src/web/static/style.css`
- [X] T013 Remove out-of-scope video receiving pause API handlers from `src/web/routes.py`
- [X] T014 Remove out-of-scope video receiving pause UI controls from `src/web/templates/dashboard.html`
- [X] T015 Remove out-of-scope video receiving pause frontend behavior from `src/web/static/app.js`
- [X] T016 Remove out-of-scope video receiving state tests from `tests/test_web_routes.py`

**Checkpoint**: Foundation ready. User story implementation can now begin in priority order or in parallel by separate owners.

---

## Phase 3: User Story 1 - Retain Target Detection History (Priority: P1) MVP

**Goal**: Save only target-containing detection results, keep recent 48-hour history, and expose filtered history/detail views.

**Independent Test**: Feed mixed target/no-target detections, then confirm only target records within the latest 48 hours appear in reverse chronological order with class/confidence filters and detail view.

### Tests for User Story 1

- [X] T017 [P] [US1] Add unit tests for target-only insert, no-target skip, confidence validation, and bbox validation in `tests/test_detection_storage.py`
- [X] T018 [P] [US1] Add unit tests for 48-hour filtering, reverse chronological ordering, class filtering, confidence filtering, and cleanup in `tests/test_detection_storage.py`
- [X] T019 [P] [US1] Add route tests for `GET /api/detections/recent` and `GET /api/detections/{detection_id}` in `tests/test_web_routes.py`
- [X] T020 [P] [US1] Add integration test proving pipeline detections are persisted while empty frames are ignored in `tests/integration/test_agent_detection_workflows.py`

### Implementation for User Story 1

- [X] T021 [US1] Implement DetectionRecord table creation and indexes for detected time, class, and confidence in `src/web/storage.py`
- [X] T022 [US1] Implement target-only detection persistence and no-target skip behavior in `src/web/storage.py`
- [X] T023 [US1] Implement recent detection query, detection detail query, class/confidence filters, and 48-hour cleanup in `src/web/storage.py`
- [X] T024 [US1] Add detection history DTOs and `to_dict` conversions matching `contracts/web-api.openapi.yaml` in `src/web/schemas.py`
- [X] T025 [US1] Integrate target detection persistence into `WebDetectionPipeline._run` without changing camera or detector logic in `src/web/stream.py`
- [X] T026 [US1] Add authenticated `GET /api/detections/recent` and `GET /api/detections/{detection_id}` handlers in `src/web/routes.py`
- [X] T027 [US1] Replace latest-only detection page behavior with filterable recent history and detail panel in `src/web/templates/detections.html`
- [X] T028 [US1] Implement detection history fetch, filter, sort, empty state, error state, and detail rendering in `src/web/static/app.js`
- [X] T029 [US1] Add detection history responsive table and detail panel styling in `src/web/static/style.css`
- [X] T030 [US1] Document target-only retention and 48-hour history behavior in `docs/web-dashboard.md`

**Checkpoint**: User Story 1 is independently functional and can be demoed as the MVP.

---

## Phase 4: User Story 2 - Analyze Pest and Disease Risk (Priority: P2)

**Goal**: Provide asynchronous Agent analysis over recent 48-hour detection evidence with saved severity, evidence, recommendations, and related detection links.

**Independent Test**: Seed recent detections, start manual analysis, then verify the saved result includes pest/disease name, severity, evidence, recommendation, manual-review flag, analysis time, and related detections without blocking realtime monitoring.

### Tests for User Story 2

- [X] T031 [P] [US2] Add unit tests for evidence packet construction from recent detections in `tests/test_agent_analysis.py`
- [X] T032 [P] [US2] Add unit tests for severity mapping, insufficient evidence handling, high-risk trigger detection, and scheduled trigger request creation in `tests/test_agent_analysis.py`
- [X] T033 [P] [US2] Add route tests for `POST /api/agent/analyze`, `GET /api/agent/analysis/recent`, and `GET /api/agent/analysis/{analysis_id}` in `tests/test_web_routes.py`
- [X] T034 [P] [US2] Add integration test proving analysis jobs run without blocking realtime detection polling in `tests/integration/test_agent_detection_workflows.py`

### Implementation for User Story 2

- [X] T035 [US2] Implement AgentAnalysisResult table creation, persistence, recent query, detail query, and related detection references in `src/web/storage.py`
- [X] T036 [US2] Implement evidence packet builder for counts, frequency, confidence, time distribution, crop stage, and environment context in `src/web/agent_analysis.py`
- [X] T037 [US2] Implement deterministic risk rules for high-risk trigger and severity normalization in `src/web/agent_analysis.py`
- [X] T038 [US2] Implement bounded asynchronous analysis job runner with pending, running, completed, and failed states in `src/web/agent_analysis.py`
- [X] T039 [US2] Add analysis DTOs and request/response serialization matching `contracts/web-api.openapi.yaml` in `src/web/schemas.py`
- [X] T040 [US2] Add authenticated analysis API handlers in `src/web/routes.py`
- [X] T041 [US2] Add high-risk analysis trigger hook after target detection persistence without blocking inference in `src/web/stream.py`
- [X] T042 [US2] Add Agent analysis page template with result list, severity, evidence, recommendation, manual review, and manual start control in `src/web/templates/analysis.html`
- [X] T043 [US2] Implement analysis page fetch, manual start, loading, empty, failed, and completed rendering in `src/web/static/app.js`
- [X] T044 [US2] Add analysis severity, evidence, and recommendation styling in `src/web/static/style.css`
- [X] T045 [US2] Document Agent analysis triggers, evidence scope, and failure behavior in `docs/web-dashboard.md`

**Checkpoint**: User Story 2 can be tested with seeded recent detections and does not interrupt realtime monitoring.

---

## Phase 5: User Story 3 - Ask Questions Grounded in Detection and Analysis Data (Priority: P2)

**Goal**: Provide Agent Q&A over recent detections and analysis results, with saved grounded answers, citations, recommendations, and uncertainty.

**Independent Test**: Ask questions about recent detections and analyses, verify answers cite related records and use the required insufficient-data response when evidence is not enough.

### Tests for User Story 3

- [X] T046 [P] [US3] Add unit tests for chat evidence packet construction from recent detections and analyses in `tests/test_agent_chat.py`
- [X] T047 [P] [US3] Add unit tests for grounded answer shape, citation IDs, uncertainty notes, and insufficient-data response in `tests/test_agent_chat.py`
- [X] T048 [P] [US3] Add route tests for `POST /api/agent/chat` in `tests/test_web_routes.py`
- [X] T049 [P] [US3] Add integration test for asking recent-risk and today-vs-yesterday questions in `tests/integration/test_agent_detection_workflows.py`

### Implementation for User Story 3

- [X] T050 [US3] Implement AgentChatMessage table creation, persistence, and related detection/analysis references in `src/web/storage.py`
- [X] T051 [US3] Implement chat evidence builder over latest 48-hour detections and saved analyses in `src/web/agent_chat.py`
- [X] T052 [US3] Implement grounded answer generation interface, uncertainty handling, citation selection, and insufficient-data fallback in `src/web/agent_chat.py`
- [X] T053 [US3] Add chat DTOs and request/response serialization matching `contracts/web-api.openapi.yaml` in `src/web/schemas.py`
- [X] T054 [US3] Add authenticated `POST /api/agent/chat` handler in `src/web/routes.py`
- [X] T055 [US3] Add Agent Q&A page template with chat input, answer, evidence, related detections, and related analyses in `src/web/templates/chat.html`
- [X] T056 [US3] Implement chat submit, loading, error, insufficient-data, evidence, and citation rendering in `src/web/static/app.js`
- [X] T057 [US3] Add chat layout, message, evidence, and citation styling in `src/web/static/style.css`
- [X] T058 [US3] Document grounded Q&A scope, insufficient-data behavior, and supported example questions in `docs/web-dashboard.md`

**Checkpoint**: User Story 3 can answer from recent evidence and refuses unsupported conclusions.

---

## Phase 6: User Story 4 - Switch Interface Language (Priority: P3)

**Goal**: Provide Chinese/English switching across login, dashboard, history, Agent analysis, Agent chat, labels, prompts, errors, and fixed statuses with browser-local persistence.

**Independent Test**: Switch language on supported pages, refresh the browser, and verify visible text and fixed statuses remain in the selected language.

### Tests for User Story 4

- [X] T059 [P] [US4] Add unit tests for supported languages, fallback language, status-code translation, and missing-key fallback in `tests/test_i18n.py`
- [X] T060 [P] [US4] Add route tests for `GET /api/i18n/languages` in `tests/test_web_routes.py`
- [X] T061 [P] [US4] Add frontend-oriented integration test for persisted language selection across dashboard, detections, analysis, and chat pages in `tests/integration/test_agent_detection_workflows.py`

### Implementation for User Story 4

- [X] T062 [US4] Implement supported language metadata, translation keys, status-code labels, and missing-key fallback in `src/web/i18n.py`
- [X] T063 [US4] Add language DTOs matching `contracts/web-api.openapi.yaml` in `src/web/schemas.py`
- [X] T064 [US4] Add public `GET /api/i18n/languages` handler in `src/web/routes.py`
- [X] T065 [US4] Add language switcher markup and translatable data attributes to `src/web/templates/login.html`
- [X] T066 [US4] Add language switcher markup and translatable data attributes to `src/web/templates/dashboard.html`
- [X] T067 [US4] Add translatable labels, filters, empty states, and errors to `src/web/templates/detections.html`
- [X] T068 [US4] Add translatable labels, controls, statuses, and errors to `src/web/templates/analysis.html`
- [X] T069 [US4] Add translatable labels, prompts, answer sections, and errors to `src/web/templates/chat.html`
- [X] T070 [US4] Implement browser-local language persistence, immediate text switching, fixed status translation, and chat language propagation in `src/web/static/app.js`
- [X] T071 [US4] Add language switcher styling and responsive checks for translated text lengths in `src/web/static/style.css`
- [X] T072 [US4] Document language switching behavior and browser-local persistence in `docs/web-dashboard.md`

**Checkpoint**: User Story 4 works across all supported pages and persists after refresh.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Final validation, documentation, performance checks, and cleanup across all stories.

- [X] T073 [P] Add hardware validation assertions for continued inference, continued persistence, and Agent non-blocking behavior in `tests/hardware/test_web_dashboard_runtime.py`
- [X] T074 [P] Add performance budget validation for storage writes, polling, Agent background jobs, and <=10% single-client overhead in `tests/unit/test_performance_budget.py`
- [X] T075 [P] Update quickstart validation notes with final commands and expected outcomes in `specs/003-agent-detection-dashboard/quickstart.md`
- [X] T076 Review all new API responses for stable status codes, localized user-facing messages, and authentication behavior in `src/web/routes.py`
- [X] T077 Review all new frontend UI states for loading, empty, error, disabled, success, and responsive layout in `src/web/static/app.js`
- [ ] T078 Run focused automated tests from quickstart and record any command deviations in `docs/web-dashboard.md`
- [ ] T079 Run Jetson hardware validation commands from quickstart and record FPS, inference continuity, and memory observations in `docs/web-dashboard.md`

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies; can start immediately.
- **Foundational (Phase 2)**: Depends on Setup completion; blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational; establishes detection history MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational and US1 detection history.
- **User Story 3 (Phase 5)**: Depends on Foundational, US1 detection history, and US2 saved analysis for full evidence.
- **User Story 4 (Phase 6)**: Depends on Foundational; can run alongside US1-US3, but final checks require all pages.
- **Polish (Phase 7)**: Depends on all desired user stories being complete.

### User Story Dependencies

- **US1 Retain Target Detection History**: Starts after Foundation; no dependency on other user stories.
- **US2 Analyze Pest and Disease Risk**: Starts after US1 because analysis evidence comes from recent detection history.
- **US3 Ask Grounded Questions**: Starts after US1 and US2 because chat evidence includes detections and analysis results.
- **US4 Switch Interface Language**: Starts after Foundation and can run alongside US1-US3, but final checks require all pages.

### Within Each User Story

- Tests must be written first and fail before implementation where practical.
- Data/schema tasks precede service tasks.
- Service tasks precede route tasks.
- Route tasks precede frontend integration tasks.
- UX and documentation tasks complete the story checkpoint.

### Parallel Opportunities

- T002, T003, T004, and T005 can run in parallel after T001 is understood.
- T010, T011, and T012 can run in parallel after T006-T009 are scoped.
- US1 tests T017-T020 can run in parallel.
- US2 tests T031-T034 can run in parallel.
- US3 tests T046-T049 can run in parallel.
- US4 tests T059-T061 can run in parallel.
- Template/static styling work can run in parallel with backend service implementation when file ownership is coordinated.

---

## Parallel Example: User Story 1

```text
Task: "T017 [P] [US1] Add unit tests for target-only insert, no-target skip, confidence validation, and bbox validation in tests/test_detection_storage.py"
Task: "T019 [P] [US1] Add route tests for GET /api/detections/recent and GET /api/detections/{detection_id} in tests/test_web_routes.py"
Task: "T020 [P] [US1] Add integration test proving pipeline detections are persisted while empty frames are ignored in tests/integration/test_agent_detection_workflows.py"
```

## Parallel Example: User Story 2

```text
Task: "T031 [P] [US2] Add unit tests for evidence packet construction from recent detections in tests/test_agent_analysis.py"
Task: "T033 [P] [US2] Add route tests for POST /api/agent/analyze, GET /api/agent/analysis/recent, and GET /api/agent/analysis/{analysis_id} in tests/test_web_routes.py"
Task: "T042 [US2] Add Agent analysis page template with result list, severity, evidence, recommendation, manual review, and manual start control in src/web/templates/analysis.html"
```

## Parallel Example: User Story 3

```text
Task: "T046 [P] [US3] Add unit tests for chat evidence packet construction from recent detections and analyses in tests/test_agent_chat.py"
Task: "T048 [P] [US3] Add route tests for POST /api/agent/chat in tests/test_web_routes.py"
Task: "T055 [US3] Add Agent Q&A page template with chat input, answer, evidence, related detections, and related analyses in src/web/templates/chat.html"
```

## Parallel Example: User Story 4

```text
Task: "T059 [P] [US4] Add unit tests for supported languages, fallback language, status-code translation, and missing-key fallback in tests/test_i18n.py"
Task: "T065 [US4] Add language switcher markup and translatable data attributes to src/web/templates/login.html"
Task: "T070 [US4] Implement browser-local language persistence, immediate text switching, fixed status translation, and chat language propagation in src/web/static/app.js"
```

---

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational.
3. Complete Phase 3: US1 Retain Target Detection History.
4. Stop and validate target-only persistence, 48-hour filtering, filters, details, and no-target skip.
5. Demo the detection history MVP before adding Agent features.

### Incremental Delivery

1. Add US1 to establish durable recent evidence.
2. Add US2 to produce saved Agent analysis from the recent evidence.
3. Add US3 to answer grounded questions from detections and analyses.
4. Add US4 to localize the complete user-facing workflow.

### Parallel Team Strategy

1. Complete Setup and Foundational work together.
2. Assign US1 backend storage/pipeline work first.
3. Start US2 analysis service once US1 storage contracts stabilize.
4. Start US3 chat service once US2 analysis storage contracts stabilize.
5. Run US4 frontend/i18n work alongside page implementation, with final pass after all pages exist.

---

## Notes

- [P] tasks use different files or can be implemented without depending on incomplete tasks.
- [US1] through [US4] labels map to the user stories in `spec.md`.
- Each user story has tests, backend behavior, route contracts, frontend behavior, UX states, and documentation tasks.
- Avoid changing existing camera, detector, login, or overlay logic except at documented extension points.
