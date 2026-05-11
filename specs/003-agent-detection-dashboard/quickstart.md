# Quickstart: Agent Detection Dashboard

## Prerequisites

- Existing Web dashboard setup from `specs/002-web-dashboard-auth/quickstart.md`
- Valid Web dashboard username, password, and session secret environment variables
- Jetson runtime dependencies for the existing camera and TensorRT pipeline
- Test environment with `pytest` and FastAPI TestClient support

## Run the Dashboard Locally With Mocks

1. Set Web credentials and session secret for the test app.
2. Start the Web app using mocked camera/detector fixtures or the existing test client helpers.
3. Log in through `/login`.
4. Open `/dashboard` and confirm realtime status and detection list render.
5. Open `/detections` and confirm only target detections from the latest 48 hours appear.
6. Filter detection history by class and minimum confidence, then open a detection detail.
7. Open the Agent analysis page, start manual analysis, and confirm the saved result includes severity, evidence, recommendation, and manual-review advice.
8. Open the Agent Q&A page and ask about recent pests or diseases; confirm the answer cites related detections and analyses.
9. Switch between Chinese and English and refresh; confirm the selected language persists.

## Contract Checks

Validate the Web API against `contracts/web-api.openapi.yaml` during route tests. Required authenticated endpoints:

- `GET /api/detections/recent?hours=48`
- `GET /api/detections/{detection_id}`
- `POST /api/agent/analyze`
- `GET /api/agent/analysis/recent?hours=48`
- `GET /api/agent/analysis/{analysis_id}`
- `POST /api/agent/chat`
- `GET /api/i18n/languages`

## Automated Test Commands

```powershell
pytest tests/test_detection_storage.py tests/test_agent_analysis.py tests/test_agent_chat.py tests/test_i18n.py tests/test_web_routes.py
pytest tests/integration/test_web_pipeline.py tests/integration/test_agent_detection_workflows.py
```

## Hardware Validation

Run on the Jetson target after automated tests pass:

```powershell
pytest tests/hardware/test_web_dashboard_runtime.py --run-jetson
pytest tests/hardware/test_realtime_fps.py --run-jetson
pytest tests/hardware/test_memory_stability.py --run-jetson
```

Hardware validation must confirm:

- Target detections continue to appear in realtime results and recent history.
- Empty frames are not written to detection history.
- Displayed FPS and single-client overhead remain within the existing performance budget.
- Analysis and Q&A interactions do not interrupt realtime monitoring.

## Implementation Notes

- Default persistence uses `web.storage_path` from `configs/jetson_orin_nano.yaml`.
- Agent responses are grounded in recent detections and saved analysis records.
- Browser language selection is stored locally and does not change the operator account profile.
