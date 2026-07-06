"""A simple fence, honest about being a simple fence.

This is a fixed-window counter living inside one function instance. It is fast
and it is local, which also means it counts alone. Scale out and each instance
keeps its own tally, none of them talking. Good enough to keep one instance
from stampeding. Not a global throttle. For that, put Azure API Management out
front. Do not ask this fence to hold back a flood it was never built for.
"""

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
