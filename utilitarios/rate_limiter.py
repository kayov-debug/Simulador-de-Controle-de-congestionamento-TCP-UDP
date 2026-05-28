"""Simple token-bucket rate limiter."""

from __future__ import annotations

import threading
import time


class RateLimiter:
    def __init__(self, rate_per_second: float, capacity: float | None = None) -> None:
        self.rate_per_second = max(float(rate_per_second), 0.0)
        self.capacity = float(capacity if capacity is not None else max(rate_per_second, 1.0))
        self._tokens = self.capacity
        self._updated_at = time.time()
        self._lock = threading.Lock()

    def allow(self, cost: float = 1.0) -> bool:
        if self.rate_per_second <= 0:
            return True

        with self._lock:
            now = time.time()
            elapsed = max(now - self._updated_at, 0.0)
            self._updated_at = now
            self._tokens = min(self.capacity, self._tokens + elapsed * self.rate_per_second)
            if self._tokens >= cost:
                self._tokens -= cost
                return True
            return False

    def wait_time(self, cost: float = 1.0) -> float:
        if self.rate_per_second <= 0:
            return 0.0
        with self._lock:
            if self._tokens >= cost:
                return 0.0
            missing = cost - self._tokens
            return missing / self.rate_per_second
