from __future__ import annotations

from dataclasses import dataclass

from src.utils.config import CameraStream
from src.utils.logging import ErrorCategory, RuntimeErrorInfo


def build_gstreamer_pipeline(stream: CameraStream) -> str:
    stream.validate()
    return (
        f"nvarguscamerasrc sensor-id={stream.sensor_id} ! "
        f"video/x-raw(memory:NVMM), width=(int){stream.width}, height=(int){stream.height}, "
        f"framerate=(fraction){stream.fps}/1 ! "
        f"nvvidconv flip-method={stream.flip_method} ! "
        "video/x-raw, format=(string)BGRx ! videoconvert ! "
        "video/x-raw, format=(string)BGR ! appsink drop=true sync=false"
    )


@dataclass
class CSICamera:
    stream: CameraStream
    capture: object | None = None

    def open(self):
        try:
            import cv2

            self.stream.pipeline = build_gstreamer_pipeline(self.stream)
            self.capture = cv2.VideoCapture(self.stream.pipeline, cv2.CAP_GSTREAMER)
            if not self.capture.isOpened():
                raise RuntimeError("CSI camera could not be opened")
            self.stream.connected = True
            return self
        except Exception as exc:
            raise RuntimeErrorInfo(
                ErrorCategory.CAMERA,
                f"failed to open CSI camera: {exc}",
                "check camera connection, sensor_id, and GStreamer/OpenCV support",
            ) from exc

    def read(self):
        if self.capture is None:
            raise RuntimeErrorInfo(ErrorCategory.CAMERA, "camera is not open", "call open() before read()")
        ok, frame = self.capture.read()
        if not ok or frame is None:
            raise RuntimeErrorInfo(ErrorCategory.CAMERA, "failed to read frame", "check CSI camera stability")
        return frame

    def release(self) -> None:
        if self.capture is not None:
            self.capture.release()
        self.stream.connected = False
