from __future__ import annotations

from typing import Iterable

from src.utils.config import DetectionResult


def format_label(detection: DetectionResult) -> str:
    return f"{detection.class_name} {detection.confidence:.2f}"


def draw_overlay(frame, detections: Iterable[DetectionResult], fps: float = 0.0):
    detections = list(detections)
    try:
        import cv2

        height, width = frame.shape[:2]
        for detection in detections:
            det = detection.clipped(width, height)
            x1, y1, x2, y2 = det.bbox
            cv2.rectangle(frame, (x1, y1), (x2, y2), (0, 255, 0), 2)
            cv2.putText(frame, format_label(det), (x1, max(15, y1 - 5)), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 1)
        cv2.putText(frame, f"FPS: {fps:.1f}", (10, 24), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
        cv2.putText(
            frame,
            f"Objects: {len(detections)}",
            (10, 52),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
    except Exception:
        # Minimal non-GUI fallback for tests without OpenCV drawing support.
        for detection in detections:
            x1, y1, x2, y2 = detection.clipped(frame.shape[1], frame.shape[0]).bbox
            frame[y1 : y2 + 1, x1 : x2 + 1] = 255
    return frame


def rendered_object_count(detections: Iterable[DetectionResult]) -> int:
    return len(list(detections))
