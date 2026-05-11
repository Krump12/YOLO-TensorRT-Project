from datetime import datetime, timedelta, timezone

from src.utils.config import DetectionResult
from src.web.storage import WebStorage


def clock_at(value):
    return lambda: value


def test_save_detections_skips_empty_frames_and_validates_bbox(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3")

    assert storage.save_detections([], detected_at=1_700_000_000.0, camera_id="cam", device_id="dev") == []

    rows = storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 1.5)],
        detected_at=1_700_000_000.0,
        camera_id="cam",
        device_id="dev",
    )

    assert len(rows) == 1
    assert rows[0]["class_name"] == "aphid"
    assert rows[0]["confidence"] == 1.0
    assert rows[0]["bbox"] == {"x1": 1, "y1": 2, "x2": 3, "y2": 4}


def test_recent_detections_filters_48_hours_class_confidence_and_cleanup(tmp_path):
    now = datetime(2026, 5, 11, 10, 0, tzinfo=timezone.utc)
    storage = WebStorage(tmp_path / "web.sqlite3", clock=clock_at(now))
    storage.save_detections(
        [DetectionResult(1, (1, 2, 3, 4), 0, "aphid", 0.9)],
        detected_at=(now - timedelta(hours=1)).timestamp(),
        camera_id="cam",
        device_id="dev",
    )
    storage.save_detections(
        [DetectionResult(2, (1, 2, 3, 4), 1, "rust", 0.6)],
        detected_at=(now - timedelta(hours=2)).timestamp(),
        camera_id="cam",
        device_id="dev",
    )
    storage.save_detections(
        [DetectionResult(3, (1, 2, 3, 4), 1, "rust", 0.95)],
        detected_at=(now - timedelta(hours=60)).timestamp(),
        camera_id="cam",
        device_id="dev",
    )

    recent = storage.recent_detections(hours=48)
    assert [row["class_name"] for row in recent] == ["aphid", "rust"]
    assert [row["class_name"] for row in storage.recent_detections(hours=48, class_name="rust")] == ["rust"]
    assert [row["class_name"] for row in storage.recent_detections(hours=48, min_confidence=0.8)] == ["aphid"]
    assert storage.cleanup_old_detections(hours=48) == 1


def test_detection_detail_returns_saved_record(tmp_path):
    storage = WebStorage(tmp_path / "web.sqlite3")
    saved = storage.save_detections(
        [DetectionResult(7, (1, 2, 3, 4), 0, "aphid", 0.8)],
        detected_at=1_700_000_000.0,
        camera_id="cam",
        device_id="dev",
    )[0]

    detail = storage.detection_detail(saved["detection_id"])

    assert detail["detection_id"] == saved["detection_id"]
    assert detail["frame_id"] == "7"


def test_save_detections_supports_legacy_has_frame_column(tmp_path):
    storage = WebStorage(tmp_path / "legacy.sqlite3")
    with storage._lock, storage._conn:
        storage._conn.execute("DROP TABLE detections")
        storage._conn.execute(
            """
            CREATE TABLE detections (
                id TEXT PRIMARY KEY,
                detected_at TEXT NOT NULL,
                class_name TEXT NOT NULL,
                confidence REAL NOT NULL,
                bbox_x1 INTEGER NOT NULL,
                bbox_y1 INTEGER NOT NULL,
                bbox_x2 INTEGER NOT NULL,
                bbox_y2 INTEGER NOT NULL,
                frame_id TEXT,
                image_id TEXT,
                camera_id TEXT NOT NULL,
                device_id TEXT NOT NULL,
                created_at TEXT NOT NULL,
                has_frame INTEGER NOT NULL
            )
            """
        )

    saved = storage.save_detections(
        [DetectionResult(8, (1, 2, 3, 4), 0, "aphid", 0.8)],
        detected_at=1_700_000_000.0,
        camera_id="cam",
        device_id="dev",
    )

    assert saved[0]["class_name"] == "aphid"
    assert storage.recent_detections(hours=48) == []
