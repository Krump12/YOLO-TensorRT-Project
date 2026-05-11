# Implementation Plan: Agent Detection Dashboard

**Branch**: `004-agent-detection-dashboard` | **Date**: 2026-05-11 | **Spec**: [spec.md](spec.md)
**Input**: Feature specification from `/specs/003-agent-detection-dashboard/spec.md`

**Note**: This template is filled in by the `/speckit-plan` command. See `.specify/templates/plan-template.md` for the execution workflow.

## Summary

Extend the existing login-protected YOLO TensorRT Web dashboard with persistent 48-hour target-only detection history, asynchronous Agent pest/disease analysis, grounded Agent Q&A, and Chinese/English interface switching. The implementation keeps the existing CSI camera, TensorRT inference pipeline, login, and base Web structure intact, then adds Web storage, Agent services, API routes, templates, static UI behavior, and i18n support under the existing `src/web/` module.

## Technical Context

**Language/Version**: Python 3.8+ in JetPack-compatible environment, with browser-side HTML/CSS/JavaScript colocated under `src/web/static` and `src/web/templates`  
**Primary Dependencies**: Existing TensorRT/CUDA/OpenCV/NumPy/PyYAML stack plus the current FastAPI, Starlette sessions/templates, python-multipart, and pytest/TestClient Web testing stack; use Python standard-library SQLite for local persistence  
**Storage**: Local SQLite database file for detection history, Agent analysis, and Agent chat records; browser local storage for language preference  
**Testing**: pytest unit and integration tests with mocked camera, detector, storage clock, Agent provider, and Web app TestClient; hardware tests remain under existing `--run-jetson` flow  
**Target Platform**: NVIDIA Jetson Orin Nano running Ubuntu + JetPack with one CSI camera; authenticated browser clients on the local network  
**Project Type**: Single Python edge-runtime application with an integrated Web service and static/template frontend  
**Performance Goals**: Preserve current realtime monitoring goals: 1080P camera input, at least 20 browser-displayed FPS under normal target-device operation, latest detection table updates within 1 second for 95% of normal updates, shutdown releases resources within 3 seconds, and one dashboard client causes no more than 10% FPS reduction versus non-Web runtime  
**Constraints**: Do not rewrite YOLO/TensorRT inference, CSI camera reading, login, or base Web structure; do not open the CSI camera twice; Agent analysis and chat must not block inference; recent views use a rolling 48-hour window; no unbounded frame, history, analysis, or chat queues  
**Scale/Scope**: One Jetson device, one CSI camera, one active detector pipeline, one configured operator account for v1, a small number of local browser clients, target-only history for the latest 48 hours, and grounded Agent responses over recent data

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- **Code Quality**: PASS. The design keeps ownership under the existing `src/web/` module and adds focused modules for storage, Agent analysis, Agent chat, and i18n. Existing `WebDetectionPipeline`, authentication, camera, detector, and overlay code remain the integration points instead of being rewritten.
- **Testing**: PASS. Required tests cover target-only persistence, 48-hour filtering/cleanup, API contracts, Agent analysis grounding, Agent chat insufficient-data behavior, i18n persistence/translation, and integration behavior with mocked camera/detector/storage.
- **UX Consistency**: PASS. New pages use the existing template/static layout and define loading, empty, error, disabled, and success states for realtime monitoring, history filters/details, analysis jobs/results, chat answers, and language switching.
- **Performance**: PASS. The plan preserves the existing 20 displayed FPS and <=10% single-client overhead budget, uses target-only writes, bounded background Agent work, default 48-hour queries, and mocked plus hardware validation for inference continuity.
- **Maintainability**: PASS. Storage boundaries, status codes, Agent evidence references, and language keys are explicit. Failure modes are observable through API status, page error states, logs, and saved analysis/chat metadata.

## Project Structure

### Documentation (this feature)

```text
specs/003-agent-detection-dashboard/
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
    |-- storage.py
    |-- agent_analysis.py
    |-- agent_chat.py
    |-- i18n.py
    |-- static/
    |   |-- app.js
    |   `-- style.css
    `-- templates/
        |-- dashboard.html
        |-- detections.html
        |-- analysis.html
        |-- chat.html
        `-- login.html

tests/
|-- test_detection_storage.py
|-- test_agent_analysis.py
|-- test_agent_chat.py
|-- test_i18n.py
|-- test_web_routes.py
|-- integration/
|   |-- test_web_pipeline.py
|   `-- test_agent_detection_workflows.py
`-- hardware/
    `-- test_web_dashboard_runtime.py
```

**Structure Decision**: Continue with the existing single Python edge-runtime layout. The Web feature remains colocated under `src/web/` because the current authenticated dashboard already lives there and imports the existing runtime packages directly. No separate frontend project is introduced; static JavaScript remains sufficient for the v1 dashboard interactions.

## Complexity Tracking

> **Fill ONLY if Constitution Check has violations that must be justified**

| Violation | Why Needed | Simpler Alternative Rejected Because |
|-----------|------------|-------------------------------------|
| None | N/A | N/A |

## Phase 0: Research Summary

Research decisions are captured in [research.md](research.md). Key outcomes:

- Use local SQLite storage by default for target-only detection history, Agent analysis records, and chat transcripts because the edge device needs simple durable local persistence without adding a managed database service.
- Persist only target detections at the Web pipeline boundary so empty frames are excluded before they consume storage or appear in history.
- Use rolling 48-hour query filters plus cleanup so user-visible correctness does not depend on a scheduled cleanup task.
- Run Agent analysis/chat work through bounded background tasks and deterministic evidence packets over recent detections/analyses, so inference remains independent and answers can be tested for grounding.
- Implement language switching with browser-local preference, frontend translation keys, and stable backend status codes.

## Phase 1: Design Summary

Design artifacts are captured in:

- [data-model.md](data-model.md)
- [contracts/web-api.openapi.yaml](contracts/web-api.openapi.yaml)
- [quickstart.md](quickstart.md)

Post-design Constitution Check: PASS. The design keeps storage and Agent modules scoped, documents authenticated API contracts, defines explicit entity relationships and validation rules, keeps UI state behavior consistent with the current dashboard, and includes automated plus hardware validation paths. No complexity exceptions were introduced.
