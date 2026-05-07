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
pytest tests/test_web_auth.py tests/test_web_routes.py tests/test_detection_result_schema.py tests/integration/test_web_pipeline.py
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
