from pathlib import Path

from fastapi.testclient import TestClient

from src.utils.config import AppConfig, CameraStream, DetectionResult, WebConfig
from src.web.app import create_app
from src.web.storage import WebStorage
from src.web.stream import LatestStateBuffer


def make_client(monkeypatch, tmp_path=None):
    monkeypatch.setenv("YOLO_WEB_PASSWORD", "secret")
    monkeypatch.setenv("YOLO_WEB_SESSION_SECRET", "test-session-secret")
    config = AppConfig(
        model_path=Path("models/best.pt"),
        engine_path=Path("models/best.engine"),
        classes_path=Path("configs/classes.yaml"),
        camera=CameraStream(),
        web=WebConfig(username="admin", stream_fps=1000),
    )
    state = LatestStateBuffer()
    state.update(
        frame_id=1,
        source_timestamp=1_700_000_000.0,
        jpeg_bytes=b"fake-jpeg",
        detections=[DetectionResult(1, (10, 20, 30, 40), 0, "person", 0.91)],
        fps=23.5,
        camera_running=True,
        detector_loaded=True,
    )
    storage = WebStorage((tmp_path / "web.sqlite3") if tmp_path else ":memory:")
    storage.save_detections(
        [DetectionResult(1, (10, 20, 30, 40), 0, "person", 0.91)],
        detected_at=None,
        camera_id=config.web.camera_id,
        device_id=config.web.device_id,
    )
    client = TestClient(create_app(config, latest_state=state, storage=storage, start_pipeline=False))
    return client


def login(client):
    response = client.post("/login", data={"username": "admin", "password": "secret"}, follow_redirects=False)
    assert response.status_code == 302


def test_root_redirects_to_login_when_unauthenticated(monkeypatch):
    client = make_client(monkeypatch)

    response = client.get("/", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"


def test_protected_pages_redirect_when_unauthenticated(monkeypatch):
    client = make_client(monkeypatch)

    for path in ["/dashboard", "/detections", "/video_feed"]:
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 302
        assert response.headers["location"] == "/login"


def test_protected_apis_return_401_when_unauthenticated(monkeypatch):
    client = make_client(monkeypatch)

    for path in ["/api/detections/latest", "/api/status"]:
        response = client.get(path)
        assert response.status_code == 401


def test_authenticated_dashboard_access(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert "Live Detection" in response.text


def test_authenticated_video_feed_returns_mjpeg(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    with client.stream("GET", "/video_feed?once=1") as response:
        chunk = next(response.iter_bytes())

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("multipart/x-mixed-replace")
    assert b"Content-Type: image/jpeg" in chunk
    assert b"fake-jpeg" in chunk


def test_status_returns_runtime_fields(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    data = client.get("/api/status").json()

    assert data["camera_running"] is True
    assert data["detector_loaded"] is True
    assert data["fps"] == 23.5
    assert data["target_count"] == 1


def test_latest_detections_returns_required_json(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    data = client.get("/api/detections/latest").json()

    assert data["timestamp"].startswith("2023-11-14T")
    assert data["fps"] == 23.5
    assert data["target_count"] == 1
    assert data["detections"][0]["class_name"] == "person"
    assert data["detections"][0]["confidence"] == 0.91
    assert data["detections"][0]["bbox"] == {"x1": 10, "y1": 20, "x2": 30, "y2": 40}


def test_detections_page_renders_history_state(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    response = client.get("/detections")

    assert response.status_code == 200
    assert "No target detections in the latest 48 hours" in response.text
    assert "Detection History" in response.text


def test_recent_detection_routes_return_history(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    listing = client.get("/api/detections/recent?hours=48").json()
    detection_id = listing["detections"][0]["detection_id"]
    detail = client.get(f"/api/detections/{detection_id}").json()

    assert listing["detections"][0]["class_name"] == "person"
    assert detail["detection_id"] == detection_id


def test_agent_analysis_routes(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    accepted = client.post("/api/agent/analyze", json={"hours": 48}).json()
    recent = client.get("/api/agent/analysis/recent?hours=48").json()
    detail = client.get(f"/api/agent/analysis/{accepted['analysis_id']}").json()

    assert accepted["analysis_id"]
    assert "analyses" in recent
    assert detail["analysis_id"] == accepted["analysis_id"]


def test_agent_chat_route(monkeypatch):
    client = make_client(monkeypatch)
    login(client)

    data = client.post("/api/agent/chat", json={"question": "Any pests?", "language": "en"}).json()

    assert data["answer"]
    assert data["language"] == "en"


def test_i18n_languages_route(monkeypatch):
    client = make_client(monkeypatch)

    data = client.get("/api/i18n/languages").json()

    assert data["default"] == "zh"
    assert {"code": "en", "label": "English"} in data["languages"]
