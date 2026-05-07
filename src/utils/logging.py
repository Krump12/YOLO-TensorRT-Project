from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class ErrorCategory(str, Enum):
    MODEL = "model"
    EXPORT = "export"
    ENGINE = "engine"
    CAMERA = "camera"
    INFERENCE = "inference"
    DISPLAY = "display"
    CONFIG = "config"
    SHUTDOWN = "shutdown"


@dataclass
class RuntimeErrorInfo(Exception):
    category: ErrorCategory
    message: str
    recommendation: str = ""
    exit_code: int = 1

    def __str__(self) -> str:
        suffix = f" Next check: {self.recommendation}" if self.recommendation else ""
        return f"[{self.category.value}] {self.message}{suffix}"


def format_error(exc: BaseException, category: ErrorCategory, recommendation: str = "") -> RuntimeErrorInfo:
    if isinstance(exc, RuntimeErrorInfo):
        return exc
    return RuntimeErrorInfo(category=category, message=str(exc), recommendation=recommendation)
