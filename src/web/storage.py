from __future__ import annotations

import json
import sqlite3
import threading
import uuid
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Iterable

from src.utils.config import DetectionResult
from src.web.schemas import timestamp_iso


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(value: str) -> datetime:
    rendered = value.replace("Z", "+00:00")
    parsed = datetime.fromisoformat(rendered)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


class WebStorage:
    def __init__(self, path: str | Path, *, clock=utc_now) -> None:
        self.path = Path(path)
        self.clock = clock
        self._lock = threading.RLock()
        if str(self.path) != ":memory:":
            self.path.parent.mkdir(parents=True, exist_ok=True)
        self._conn = sqlite3.connect(str(self.path), check_same_thread=False)
        self._conn.row_factory = sqlite3.Row
        self.initialize()

    def initialize(self) -> None:
        with self._lock, self._conn:
            self._conn.executescript(
                """
                CREATE TABLE IF NOT EXISTS schema_migrations (
                    version INTEGER PRIMARY KEY,
                    applied_at TEXT NOT NULL
                );
                INSERT OR IGNORE INTO schema_migrations(version, applied_at)
                VALUES (1, CURRENT_TIMESTAMP);

                CREATE TABLE IF NOT EXISTS detections (
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
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_detections_detected_at ON detections(detected_at);
                CREATE INDEX IF NOT EXISTS idx_detections_class_name ON detections(class_name);
                CREATE INDEX IF NOT EXISTS idx_detections_confidence ON detections(confidence);

                CREATE TABLE IF NOT EXISTS agent_analysis (
                    id TEXT PRIMARY KEY,
                    analysis_time TEXT,
                    time_range_start TEXT NOT NULL,
                    time_range_end TEXT NOT NULL,
                    pest_or_disease_name TEXT,
                    severity TEXT NOT NULL,
                    conclusion TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    recommendation TEXT NOT NULL,
                    need_manual_review INTEGER NOT NULL,
                    related_detection_ids TEXT NOT NULL,
                    trigger_type TEXT NOT NULL,
                    status TEXT NOT NULL,
                    error TEXT,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agent_analysis_created_at ON agent_analysis(created_at);

                CREATE TABLE IF NOT EXISTS agent_chat_messages (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL,
                    question TEXT NOT NULL,
                    answer TEXT NOT NULL,
                    evidence TEXT NOT NULL,
                    related_detection_ids TEXT NOT NULL,
                    related_analysis_ids TEXT NOT NULL,
                    language TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS idx_agent_chat_created_at ON agent_chat_messages(created_at);
                """
            )

    def close(self) -> None:
        with self._lock:
            self._conn.close()

    def save_detections(
        self,
        detections: Iterable[DetectionResult],
        *,
        detected_at: float | str | None,
        camera_id: str,
        device_id: str,
        image_id: str | None = None,
    ) -> list[dict[str, object]]:
        rows: list[dict[str, object]] = []
        rendered_detected_at = timestamp_iso(detected_at)
        created_at = self.clock().isoformat()
        for detection in detections:
            confidence = max(0.0, min(1.0, float(detection.confidence)))
            x1, y1, x2, y2 = (int(v) for v in detection.bbox)
            if x1 > x2 or y1 > y2:
                raise ValueError("invalid bounding box coordinates")
            row = {
                "detection_id": str(uuid.uuid4()),
                "detected_at": rendered_detected_at,
                "class_name": str(detection.class_name),
                "confidence": confidence,
                "bbox": {"x1": x1, "y1": y1, "x2": x2, "y2": y2},
                "camera_id": camera_id,
                "device_id": device_id,
                "frame_id": str(detection.frame_id),
                "image_id": image_id,
                "created_at": created_at,
            }
            rows.append(row)
        if not rows:
            return []
        with self._lock, self._conn:
            columns = self._table_columns("detections")
            has_legacy_has_frame = "has_frame" in columns
            insert_columns = [
                "id",
                "detected_at",
                "class_name",
                "confidence",
                "bbox_x1",
                "bbox_y1",
                "bbox_x2",
                "bbox_y2",
                "frame_id",
                "image_id",
                "camera_id",
                "device_id",
                "created_at",
            ]
            if has_legacy_has_frame:
                insert_columns.append("has_frame")
            placeholders = ", ".join(f":{column}" for column in insert_columns)
            self._conn.executemany(
                f"INSERT INTO detections ({', '.join(insert_columns)}) VALUES ({placeholders})",
                [
                    {
                        "id": row["detection_id"],
                        "detected_at": row["detected_at"],
                        "class_name": row["class_name"],
                        "confidence": row["confidence"],
                        "bbox_x1": row["bbox"]["x1"],
                        "bbox_y1": row["bbox"]["y1"],
                        "bbox_x2": row["bbox"]["x2"],
                        "bbox_y2": row["bbox"]["y2"],
                        "frame_id": row["frame_id"],
                        "image_id": row["image_id"],
                        "camera_id": row["camera_id"],
                        "device_id": row["device_id"],
                        "created_at": row["created_at"],
                        "has_frame": 1 if row.get("frame_id") or row.get("image_id") else 0,
                    }
                    for row in rows
                ],
            )
        return rows

    def _table_columns(self, table_name: str) -> set[str]:
        return {
            str(row["name"])
            for row in self._conn.execute(f"PRAGMA table_info({table_name})").fetchall()
        }

    def recent_detections(
        self,
        *,
        hours: int = 48,
        class_name: str | None = None,
        min_confidence: float | None = None,
    ) -> list[dict[str, object]]:
        hours = max(1, min(48, int(hours)))
        cutoff = (self.clock() - timedelta(hours=hours)).isoformat()
        query = "SELECT * FROM detections WHERE detected_at >= ?"
        params: list[object] = [cutoff]
        if class_name:
            query += " AND class_name = ?"
            params.append(class_name)
        if min_confidence is not None:
            query += " AND confidence >= ?"
            params.append(float(min_confidence))
        query += " ORDER BY detected_at DESC, created_at DESC"
        with self._lock:
            return [self._detection_from_row(row) for row in self._conn.execute(query, params).fetchall()]

    def detection_detail(self, detection_id: str) -> dict[str, object] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM detections WHERE id = ?", (detection_id,)).fetchone()
        return self._detection_from_row(row) if row else None

    def cleanup_old_detections(self, *, hours: int = 48) -> int:
        cutoff = (self.clock() - timedelta(hours=hours)).isoformat()
        with self._lock, self._conn:
            cursor = self._conn.execute("DELETE FROM detections WHERE detected_at < ?", (cutoff,))
            return int(cursor.rowcount)

    def create_analysis(self, **values) -> dict[str, object]:
        now = self.clock().isoformat()
        analysis = {
            "analysis_id": values.get("analysis_id") or str(uuid.uuid4()),
            "analysis_time": values.get("analysis_time"),
            "time_range_start": values["time_range_start"],
            "time_range_end": values["time_range_end"],
            "pest_or_disease_name": values.get("pest_or_disease_name"),
            "severity": values.get("severity", "light"),
            "conclusion": values.get("conclusion", ""),
            "evidence": values.get("evidence", {}),
            "recommendation": values.get("recommendation", ""),
            "need_manual_review": bool(values.get("need_manual_review", True)),
            "related_detection_ids": list(values.get("related_detection_ids", [])),
            "trigger_type": values.get("trigger_type", "manual"),
            "status": values.get("status", "pending"),
            "error": values.get("error"),
            "created_at": values.get("created_at", now),
        }
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO agent_analysis (
                    id, analysis_time, time_range_start, time_range_end, pest_or_disease_name, severity,
                    conclusion, evidence, recommendation, need_manual_review, related_detection_ids,
                    trigger_type, status, error, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    analysis["analysis_id"],
                    analysis["analysis_time"],
                    analysis["time_range_start"],
                    analysis["time_range_end"],
                    analysis["pest_or_disease_name"],
                    analysis["severity"],
                    analysis["conclusion"],
                    json.dumps(analysis["evidence"], ensure_ascii=False),
                    analysis["recommendation"],
                    1 if analysis["need_manual_review"] else 0,
                    json.dumps(analysis["related_detection_ids"], ensure_ascii=False),
                    analysis["trigger_type"],
                    analysis["status"],
                    analysis["error"],
                    analysis["created_at"],
                ),
            )
        return analysis

    def update_analysis(self, analysis_id: str, **values) -> dict[str, object] | None:
        current = self.analysis_detail(analysis_id)
        if current is None:
            return None
        current.update(values)
        with self._lock, self._conn:
            self._conn.execute(
                """
                UPDATE agent_analysis
                SET analysis_time = ?, pest_or_disease_name = ?, severity = ?, conclusion = ?,
                    evidence = ?, recommendation = ?, need_manual_review = ?, related_detection_ids = ?,
                    status = ?, error = ?
                WHERE id = ?
                """,
                (
                    current.get("analysis_time"),
                    current.get("pest_or_disease_name"),
                    current.get("severity", "light"),
                    current.get("conclusion", ""),
                    json.dumps(current.get("evidence", {}), ensure_ascii=False),
                    current.get("recommendation", ""),
                    1 if current.get("need_manual_review", True) else 0,
                    json.dumps(current.get("related_detection_ids", []), ensure_ascii=False),
                    current.get("status", "pending"),
                    current.get("error"),
                    analysis_id,
                ),
            )
        return self.analysis_detail(analysis_id)

    def recent_analysis(self, *, hours: int = 48) -> list[dict[str, object]]:
        cutoff = (self.clock() - timedelta(hours=max(1, min(48, int(hours))))).isoformat()
        with self._lock:
            rows = self._conn.execute(
                "SELECT * FROM agent_analysis WHERE created_at >= ? ORDER BY created_at DESC",
                (cutoff,),
            ).fetchall()
        return [self._analysis_from_row(row) for row in rows]

    def analysis_detail(self, analysis_id: str) -> dict[str, object] | None:
        with self._lock:
            row = self._conn.execute("SELECT * FROM agent_analysis WHERE id = ?", (analysis_id,)).fetchone()
        return self._analysis_from_row(row) if row else None

    def save_chat_message(
        self,
        *,
        user_id: str,
        question: str,
        answer: str,
        evidence: dict[str, object],
        related_detection_ids: list[str],
        related_analysis_ids: list[str],
        language: str,
    ) -> dict[str, object]:
        row = {
            "message_id": str(uuid.uuid4()),
            "user_id": user_id,
            "question": question,
            "answer": answer,
            "evidence": evidence,
            "related_detection_ids": related_detection_ids,
            "related_analysis_ids": related_analysis_ids,
            "language": language,
            "created_at": self.clock().isoformat(),
        }
        with self._lock, self._conn:
            self._conn.execute(
                """
                INSERT INTO agent_chat_messages (
                    id, user_id, question, answer, evidence, related_detection_ids,
                    related_analysis_ids, language, created_at
                )
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    row["message_id"],
                    row["user_id"],
                    row["question"],
                    row["answer"],
                    json.dumps(row["evidence"], ensure_ascii=False),
                    json.dumps(row["related_detection_ids"], ensure_ascii=False),
                    json.dumps(row["related_analysis_ids"], ensure_ascii=False),
                    row["language"],
                    row["created_at"],
                ),
            )
        return row

    def _detection_from_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "detection_id": row["id"],
            "detected_at": row["detected_at"],
            "class_name": row["class_name"],
            "confidence": float(row["confidence"]),
            "bbox": {"x1": row["bbox_x1"], "y1": row["bbox_y1"], "x2": row["bbox_x2"], "y2": row["bbox_y2"]},
            "camera_id": row["camera_id"],
            "device_id": row["device_id"],
            "frame_id": row["frame_id"],
            "image_id": row["image_id"],
            "created_at": row["created_at"],
        }

    def _analysis_from_row(self, row: sqlite3.Row) -> dict[str, object]:
        return {
            "analysis_id": row["id"],
            "analysis_time": row["analysis_time"],
            "time_range_start": row["time_range_start"],
            "time_range_end": row["time_range_end"],
            "pest_or_disease_name": row["pest_or_disease_name"],
            "severity": row["severity"],
            "conclusion": row["conclusion"],
            "evidence": json.loads(row["evidence"] or "{}"),
            "recommendation": row["recommendation"],
            "need_manual_review": bool(row["need_manual_review"]),
            "related_detection_ids": json.loads(row["related_detection_ids"] or "[]"),
            "trigger_type": row["trigger_type"],
            "status": row["status"],
            "error": row["error"],
            "created_at": row["created_at"],
        }
