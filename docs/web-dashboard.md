# YOLO TensorRT Web Dashboard

## Branch

```bash
git checkout main
git pull
git checkout -b feature/web
```

If the branch already exists:

```bash
git checkout feature/web
```

## Dependencies

This repository does not currently define a dependency manifest. Install the Web
runtime packages in the active Jetson Python environment:

```bash
python -m pip install fastapi uvicorn python-multipart httpx
```

The existing TensorRT, CUDA, OpenCV, NumPy, PyYAML, and Ultralytics runtime
dependencies are still required for real camera detection.

## Environment Variables

Set the required secrets before starting the Web service:

```bash
export YOLO_WEB_PASSWORD=your_password
export YOLO_WEB_SESSION_SECRET=your_secret
export YOLO_AGENT_PROVIDER=deterministic
export YOLO_AGENT_DEFAULT_LANGUAGE=zh
```

Do not commit real secret values. Use `.env.example` only as a name reference.

## Start

```bash
python scripts/run_web_detection.py --config configs/jetson_orin_nano.yaml
```

Open:

```text
http://<jetson-ip>:8000
```

Find the Jetson IP:

```bash
hostname -I
```

## Tests

Default Web tests do not open a CSI camera or load a TensorRT engine:

```bash
pytest tests/test_web_auth.py tests/test_web_routes.py tests/test_detection_result_schema.py tests/test_detection_storage.py tests/test_video_stream_status.py tests/test_agent_analysis.py tests/test_agent_chat.py tests/test_i18n.py tests/integration/test_web_pipeline.py tests/integration/test_agent_detection_workflows.py
```

Run existing non-Web runtime tests after implementation changes:

```bash
pytest tests/unit tests/integration
```

Run Jetson-only Web validation explicitly:

```bash
pytest --run-jetson tests/hardware/test_web_dashboard_runtime.py
```

Validated in the development environment:

```bash
pytest tests/unit/test_config.py tests/test_detection_result_schema.py tests/test_web_auth.py tests/test_web_routes.py tests/integration/test_web_pipeline.py
# 22 passed

pytest tests/unit tests/integration
# 32 passed
```

`tests/test_cli.py` requires PyTorch/Ultralytics runtime dependencies and was
not collected successfully in the current non-Jetson environment.

## Troubleshooting

- Camera does not open: check the CSI cable, `camera.sensor_id`, JetPack camera
  stack, and whether another process is using the camera.
- TensorRT engine does not exist: export or copy the engine configured by
  `model.engine_path`.
- Web page has no video: confirm login succeeded, `/api/status` reports the
  camera and detector as ready, and the browser can reach port 8000.
- Login fails: confirm `web.username` and `YOLO_WEB_PASSWORD` match.
- FPS is too low: reduce `web.stream_fps` or `web.jpeg_quality`, verify FP16
  engine usage, and check Jetson CPU/GPU load.

## 48-Hour Target History

Only frames with one or more detected targets are persisted. Empty frames are
ignored. Default history, Agent analysis, and Agent Q&A use a rolling 48-hour
window, with older rows excluded from normal views and removable by cleanup.

## Agent Analysis And Q&A

Agent analysis reads recent detection evidence, computes counts, confidence,
time distribution, and severity, then stores the result with related detection
IDs. Manual, high-risk, and scheduled triggers share the same saved result
shape. Analysis failures are recorded without interrupting realtime inference.

Agent Q&A builds an evidence packet from recent detections and saved analysis
results. If evidence is insufficient, it returns the required insufficient-data
message instead of inventing a diagnosis.

## Language Switching

The Web UI supports Chinese and English. The browser stores the selected
language locally and applies it immediately across login, dashboard, history,
analysis, and chat pages. Backend fixed statuses use stable codes so the
frontend can translate them.
