# Quickstart: Web Dashboard Authentication

## Branch

```bash
git checkout main
git pull
git checkout -b feature/web
```

If `feature/web` already exists:

```bash
git checkout feature/web
```

## Environment

Set required secrets on the Jetson before starting the Web service:

```bash
export YOLO_WEB_PASSWORD=your_password
export YOLO_WEB_SESSION_SECRET=your_secret
```

The repository should include `.env.example` documenting these names, but real
secret values must not be committed.

## Configuration

Extend `configs/jetson_orin_nano.yaml` with:

```yaml
web:
  host: 0.0.0.0
  port: 8000
  username: admin
  password_env: YOLO_WEB_PASSWORD
  stream_fps: 20
  jpeg_quality: 80
  session_secret_env: YOLO_WEB_SESSION_SECRET
```

The Web service uses the existing model, engine, camera, inference, and runtime
sections for CSI capture and TensorRT inference.

## Start

```bash
python scripts/run_web_detection.py --config configs/jetson_orin_nano.yaml
```

Open:

```text
http://<jetson-ip>:8000
```

To find the Jetson IP:

```bash
hostname -I
```

## Default Test Commands

Run Web route/schema tests without real hardware:

```bash
pytest tests/test_web_auth.py tests/test_web_routes.py tests/test_detection_result_schema.py
```

Run integration tests that use mocked camera/detector:

```bash
pytest tests/integration/test_web_pipeline.py
```

Run Jetson hardware validation explicitly:

```bash
pytest --run-jetson tests/hardware/test_web_dashboard_runtime.py
```

## Manual Acceptance Check

1. Start the Web service with required environment variables set.
2. Visit `http://<jetson-ip>:8000`.
3. Verify unauthenticated access redirects to login.
4. Log in with the configured username and password.
5. Verify the dashboard shows annotated live video, FPS, and target count.
6. Open the detections page and verify latest-frame rows update automatically.
7. Log out and verify protected pages are no longer accessible.

## Troubleshooting

- Camera does not open: check CSI connection, `sensor_id`, GStreamer/OpenCV
  support, and whether another process already owns the camera.
- TensorRT engine is missing: create or copy the `.engine` file configured in
  `model.engine_path`.
- Page has no video: confirm the dashboard is logged in, camera and detector
  status are ready, and the browser can reach the Jetson port.
- Login fails: confirm `web.username` and `YOLO_WEB_PASSWORD` match.
- FPS is low: reduce `web.stream_fps` or `web.jpeg_quality`, verify FP16 engine
  usage, and check CPU/GPU load on the Jetson.
