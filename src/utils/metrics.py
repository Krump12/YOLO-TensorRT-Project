from __future__ import annotations

import os
import time
from collections import deque
from dataclasses import dataclass, field


def current_memory_mb() -> float:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except Exception:
        return 0.0


@dataclass
class FpsCounter:
    window: int = 30
    timestamps: deque[float] = field(default_factory=deque)

    def tick(self, now: float | None = None) -> float:
        now = time.perf_counter() if now is None else now
        self.timestamps.append(now)
        while len(self.timestamps) > self.window:
            self.timestamps.popleft()
        return self.fps

    @property
    def fps(self) -> float:
        if len(self.timestamps) < 2:
            return 0.0
        elapsed = self.timestamps[-1] - self.timestamps[0]
        if elapsed <= 0:
            return 0.0
        return (len(self.timestamps) - 1) / elapsed


@dataclass
class LatencyTimer:
    started_at: float = 0.0

    def start(self) -> None:
        self.started_at = time.perf_counter()

    def stop_ms(self) -> float:
        if not self.started_at:
            return 0.0
        elapsed = (time.perf_counter() - self.started_at) * 1000
        self.started_at = 0.0
        return elapsed


@dataclass
class PerformanceBudget:
    target_fps: float = 20.0
    memory_growth_mb_limit: float = 128.0

    def evaluate(self, fps: float, memory_start_mb: float, memory_current_mb: float) -> list[str]:
        warnings: list[str] = []
        if fps and fps < self.target_fps:
            warnings.append(f"fps below target: {fps:.2f} < {self.target_fps:.2f}")
        if memory_start_mb and memory_current_mb - memory_start_mb > self.memory_growth_mb_limit:
            warnings.append(
                f"memory growth above limit: {memory_current_mb - memory_start_mb:.1f} MB > {self.memory_growth_mb_limit:.1f} MB"
            )
        return warnings


def object_count(detections: list[object]) -> int:
    return len(detections)
