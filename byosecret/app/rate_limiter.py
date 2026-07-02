from __future__ import annotations

import threading
import time


class FixedWindowRateLimiter:
    def __init__(self, limit: int, window_seconds: int) -> None:
        self.limit = limit
        self.window_seconds = window_seconds
        self._lock = threading.Lock()
        self._window_start = time.time()
        self._count = 0

    def allow_request(self) -> bool:
        now = time.time()
        with self._lock:
            if now - self._window_start >= self.window_seconds:
                self._window_start = now
                self._count = 0

            if self._count >= self.limit:
                return False

            self._count += 1
            return True
