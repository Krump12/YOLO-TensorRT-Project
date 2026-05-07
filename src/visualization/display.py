from __future__ import annotations

from src.utils.logging import ErrorCategory, RuntimeErrorInfo
from src.visualization.overlay import draw_overlay


class OpenCVDisplay:
    def __init__(self, window_name: str, exit_key: str = "q") -> None:
        self.window_name = window_name
        self.exit_key = exit_key

    def show(self, frame, detections, fps: float = 0.0) -> int:
        try:
            import cv2

            cv2.imshow(self.window_name, draw_overlay(frame, detections, fps))
            return cv2.waitKey(1)
        except Exception as exc:
            raise RuntimeErrorInfo(ErrorCategory.DISPLAY, f"display failed: {exc}", "check OpenCV GUI support") from exc

    def close(self) -> None:
        try:
            import cv2

            cv2.destroyWindow(self.window_name)
        except Exception:
            pass
