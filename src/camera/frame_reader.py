from __future__ import annotations

import queue
import threading
import time
from dataclasses import dataclass, field
from typing import Any

from src.utils.config import FramePacket


@dataclass
class LatestFrameReader:
    camera: Any
    queue_size: int = 2
    _queue: queue.Queue[FramePacket] = field(init=False)
    _stop: threading.Event = field(default_factory=threading.Event, init=False)
    _thread: threading.Thread | None = field(default=None, init=False)
    dropped_frames: int = 0
    frame_id: int = 0

    def __post_init__(self) -> None:
        if self.queue_size < 1:
            raise ValueError("queue_size must be at least 1")
        self._queue = queue.Queue(maxsize=self.queue_size)

    def start(self) -> None:
        self._stop.clear()
        self._thread = threading.Thread(target=self._run, name="csi-frame-reader", daemon=True)
        self._thread.start()

    def _put_latest(self, packet: FramePacket) -> None:
        while self._queue.full():
            try:
                self._queue.get_nowait()
                self.dropped_frames += 1
            except queue.Empty:
                break
        self._queue.put_nowait(packet)

    def _run(self) -> None:
        while not self._stop.is_set():
            frame = self.camera.read()
            height, width = frame.shape[:2]
            self.frame_id += 1
            self._put_latest(FramePacket(self.frame_id, time.time(), frame, width, height))

    def read_latest(self, timeout: float = 1.0) -> FramePacket | None:
        try:
            packet = self._queue.get(timeout=timeout)
            while True:
                packet = self._queue.get_nowait()
        except queue.Empty:
            return packet if "packet" in locals() else None

    def stop(self) -> None:
        self._stop.set()
        if self._thread is not None:
            self._thread.join(timeout=2.0)
        if hasattr(self.camera, "release"):
            self.camera.release()
