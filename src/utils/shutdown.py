from __future__ import annotations

import signal
import threading


class ShutdownController:
    def __init__(self) -> None:
        self._event = threading.Event()

    def request(self) -> None:
        self._event.set()

    @property
    def requested(self) -> bool:
        return self._event.is_set()

    def install_signal_handlers(self) -> None:
        def handler(_signum, _frame):
            self.request()

        signal.signal(signal.SIGINT, handler)
        signal.signal(signal.SIGTERM, handler)

    def check_key(self, key_code: int, exit_key: str = "q") -> bool:
        if key_code < 0:
            return False
        if key_code & 0xFF == ord(exit_key):
            self.request()
            return True
        return False
