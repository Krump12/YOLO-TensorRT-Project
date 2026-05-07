from pathlib import Path

from fastapi.testclient import TestClient

from src.utils.config import AppConfig, CameraStream, WebConfig
from src.web.app import create_app
from src.web.stream import LatestStateBuffer


def make_client(monkeypatch):
    monkeypatch.setenv("YOLO_WEB_PASSWORD", "secret")
    monkeypatch.setenv("YOLO_WEB_SESSION_SECRET", "test-session-secret")
    config = AppConfig(
        model_path=Path("models/best.pt"),
        engine_path=Path("models/best.engine"),
        classes_path=Path("configs/classes.yaml"),
        camera=CameraStream(),
        web=WebConfig(username="admin"),
    )
    return TestClient(create_app(config, latest_state=LatestStateBuffer(), start_pipeline=False))


def test_login_success_redirects_to_dashboard(monkeypatch):
    client = make_client(monkeypatch)

    response = client.post("/login", data={"username": "admin", "password": "secret"}, follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/dashboard"


def test_bad_password_cannot_login(monkeypatch):
    client = make_client(monkeypatch)

    response = client.post("/login", data={"username": "admin", "password": "bad"})

    assert response.status_code == 401
    assert "Invalid username or password" in response.text
    assert "secret" not in response.text


def test_logout_clears_session(monkeypatch):
    client = make_client(monkeypatch)
    client.post("/login", data={"username": "admin", "password": "secret"})

    response = client.post("/logout", follow_redirects=False)
    protected = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert response.headers["location"] == "/login"
    assert protected.status_code == 302
    assert protected.headers["location"] == "/login"
