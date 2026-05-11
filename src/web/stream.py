from __future__ import annotations

import threading
import time
from dataclasses import dataclass
from typing import Callable, Iterable

from src.camera.csi_camera import CSICamera
from src.camera.frame_reader import LatestFrameReader
from src.inference.tensorrt_detector import TensorRTDetector
from src.utils.config import AppConfig, DetectionResult, load_class_names
from src.utils.metrics import FpsCounter
from src.visualization.overlay import draw_overlay
from src.web.schemas import DetectionSnapshotDTO, RuntimeStatusDTO, snapshot_from_detections, timestamp_iso


@dataclass(frozen=True)
class FrameSnapshot:
    timestamp: str
    frame_id: int
    jpeg_bytes: bytes
    fps: float
    target_count: int


class LatestStateBuffer:
    def __init__(self) -> None:
        self._lock = threading.RLock()
        self._frame: FrameSnapshot | None = None
        self._detections = snapshot_from_detections([], fps=0.0)
        self._status = RuntimeStatusDTO(
            camera_running=False,
            detector_loaded=False,
            fps=0.0,
            target_count=0,
            last_update=None,
            error=None,
        )

    def update(
        self,
        *,
        frame_id: int,
        source_timestamp: float,
        jpeg_bytes: bytes | None,
        detections: Iterable[DetectionResult],
        fps: float,
        camera_running: bool,
        detector_loaded: bool,
    ) -> None:
        detection_list = list(detections)
        rendered_timestamp = timestamp_iso(source_timestamp)
        snapshot = snapshot_from_detections(detection_list, fps=fps, timestamp=rendered_timestamp)
        frame = (
            FrameSnapshot(rendered_timestamp, frame_id, jpeg_bytes, float(fps), len(detection_list))
            if jpeg_bytes is not None
            else None
        )
        status = RuntimeStatusDTO(
            camera_running=camera_running,
            detector_loaded=detector_loaded,
            fps=float(fps),
            target_count=len(detection_list),
            last_update=rendered_timestamp,
            error=None,
        )
        with self._lock:
            if frame is not None:
                self._frame = frame
            self._detections = snapshot
            self._status = status

    def set_error(self, message: str | None, *, camera_running: bool = False, detector_loaded: bool = False) -> None:
        with self._lock:
            self._status = RuntimeStatusDTO(
                camera_running=camera_running,
                detector_loaded=detector_loaded,
                fps=self._status.fps,
                target_count=self._status.target_count,
                last_update=self._status.last_update,
                error=message or None,
            )

    def latest_frame(self) -> FrameSnapshot | None:
        with self._lock:
            return self._frame

    def latest_detections(self) -> DetectionSnapshotDTO:
        with self._lock:
            return self._detections

    def status(self) -> RuntimeStatusDTO:
        with self._lock:
            return self._status

    def mjpeg_frames(self, stream_fps: float) -> Iterable[bytes]:
        delay = 1.0 / max(float(stream_fps), 1.0)
        last_frame_id: int | None = None
        while True:
            frame = self.latest_frame()
            if frame is not None and frame.frame_id != last_frame_id:
                last_frame_id = frame.frame_id
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame.jpeg_bytes + b"\r\n"
                )
            time.sleep(delay)


def encode_jpeg(frame, quality: int) -> bytes:
    try:
        import cv2

        ok, encoded = cv2.imencode(".jpg", frame, [int(cv2.IMWRITE_JPEG_QUALITY), int(quality)])
        if not ok:
            raise RuntimeError("cv2.imencode returned false")
        return bytes(encoded)
    except Exception as exc:
        raise RuntimeError(f"failed to encode JPEG frame: {exc}") from exc


class WebDetectionPipeline:
    def __init__(
        self,
        config: AppConfig,
        state: LatestStateBuffer,
        *,
        camera_factory: Callable[[AppConfig], object] | None = None,
        detector_factory: Callable[[AppConfig], object] | None = None,
        reader_factory: Callable[[object, int], LatestFrameReader] | None = None,
        jpeg_encoder: Callable[[object, int], bytes] = encode_jpeg,
        storage: object | None = None,
        analysis_service: object | None = None,
    ) -> None:
        self.config = config
        self.state = state
        self.camera_factory = camera_factory or (lambda cfg: CSICamera(cfg.camera).open())
        self.detector_factory = detector_factory or self._default_detector
        self.reader_factory = reader_factory or (lambda camera, queue_size: LatestFrameReader(camera, queue_size=queue_size))
        self.jpeg_encoder = jpeg_encoder
        self.storage = storage
        self.analysis_service = analysis_service
        self._stop = threading.Event()
        self._thread: threading.Thread | None = None
        self._reader: LatestFrameReader | None = None

    def _default_detector(self, config: AppConfig) -> TensorRTDetector:
        class_names = load_class_names(config.classes_path)
        return TensorRTDetector(
            config.engine_path,
            class_names,
            imgsz=config.imgsz,
            conf=config.conf_threshold,
            iou=config.iou_threshold,
            max_det=config.max_detections,
        ).load()

    @property
    def running(self) -> bool:
        return self._thread is not None and self._thread.is_alive()

    def start(self) -> None:
        if self.running:
            return
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="web-detection-pipeline", daemon=True)
        self._thread.start()

    def _run(self) -> None:
        detector_loaded = False
        try:
            detector = self.detector_factory(self.config)
            detector_loaded = True
            camera = self.camera_factory(self.config)
            self._reader = self.reader_factory(camera, self.config.queue_size)
            self._reader.start()
            fps = FpsCounter()
            while not self._stop.is_set():
                packet = self._reader.read_latest(timeout=0.5)
                if packet is None:
                    continue
                detections = detector.detect(packet.frame_id, packet.image)
                persisted = []
                if self.storage is not None and detections:
                    persisted = self.storage.save_detections(
                        detections,
                        detected_at=packet.timestamp,
                        camera_id=self.config.web.camera_id,
                        device_id=self.config.web.device_id,
                    )
                    if self.analysis_service is not None:
                        self.analysis_service.maybe_trigger_high_risk(persisted)
                current_fps = fps.tick()
                annotated = draw_overlay(packet.image.copy(), detections, current_fps)
                jpeg = self.jpeg_encoder(annotated, self.config.web.jpeg_quality)
                self.state.update(
                    frame_id=packet.frame_id,
                    source_timestamp=packet.timestamp,
                    jpeg_bytes=jpeg,
                    detections=detections,
                    fps=current_fps,
                    camera_running=True,
                    detector_loaded=detector_loaded,
                )
                time.sleep(max(0.0, (1.0 / max(self.config.web.stream_fps, 1.0)) - 0.001))
        except Exception as exc:
            self.state.set_error(str(exc), camera_running=False, detector_loaded=detector_loaded)
            import traceback
            traceback.print_exc()
            self.state.set_error(str(exc), camera_running=False, detector_loaded=detector_loaded)
        finally:
            if self._reader is not None:
                self._reader.stop()
            status = self.state.status()
            self.state.set_error(status.error, camera_running=False, detector_loaded=detector_loaded)

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=max(3.0, float(self.config.max_exit_seconds)))
            self._thread = None
