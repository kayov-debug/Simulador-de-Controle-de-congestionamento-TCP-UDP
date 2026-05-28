"""Metrics collection and persistence helpers."""

from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass, asdict, field
from pathlib import Path
from typing import Any


@dataclass
class MetricsSnapshot:
    started_at: float
    finished_at: float | None = None
    received_messages: int = 0
    sent_messages: int = 0
    dropped_messages: int = 0
    lost_messages: int = 0
    received_bytes: int = 0
    sent_bytes: int = 0
    latency_samples: list[float] = field(default_factory=list)
    messages_per_second: list[dict[str, float]] = field(default_factory=list)

    @property
    def duration(self) -> float:
        end_time = self.finished_at if self.finished_at is not None else time.time()
        return max(end_time - self.started_at, 0.0)

    @property
    def throughput_bps(self) -> float:
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.received_bytes / duration

    @property
    def throughput_mbps(self) -> float:
        return (self.throughput_bps * 8) / 1_000_000

    @property
    def latency_avg_ms(self) -> float:
        if not self.latency_samples:
            return 0.0
        return (sum(self.latency_samples) / len(self.latency_samples)) * 1000.0

    @property
    def messages_per_second_avg(self) -> float:
        duration = self.duration
        if duration == 0:
            return 0.0
        return self.received_messages / duration

    @property
    def total_handled_messages(self) -> int:
        return self.received_messages + self.dropped_messages + self.lost_messages

    @property
    def loss_rate_percent(self) -> float:
        total = self.received_messages + self.lost_messages
        if total == 0:
            return 0.0
        return (self.lost_messages / total) * 100.0

    @property
    def drop_rate_percent(self) -> float:
        total = self.received_messages + self.dropped_messages
        if total == 0:
            return 0.0
        return (self.dropped_messages / total) * 100.0

    def to_dict(self) -> dict[str, Any]:
        data = asdict(self)
        data["duration"] = self.duration
        data["throughput_bps"] = self.throughput_bps
        data["throughput_mbps"] = self.throughput_mbps
        data["latency_avg_ms"] = self.latency_avg_ms
        data["messages_per_second_avg"] = self.messages_per_second_avg
        data["total_handled_messages"] = self.total_handled_messages
        data["loss_rate_percent"] = self.loss_rate_percent
        data["drop_rate_percent"] = self.drop_rate_percent
        return data


class MetricsCollector:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._snapshot = MetricsSnapshot(started_at=time.time())
        self._last_rate_window = time.time()
        self._window_count = 0
        self._last_sequence_by_client: dict[int, int] = {}

    def record_sent(self, size_bytes: int) -> None:
        with self._lock:
            self._snapshot.sent_messages += 1
            self._snapshot.sent_bytes += size_bytes

    def record_received(self, size_bytes: int, latency_seconds: float | None = None) -> None:
        with self._lock:
            self._snapshot.received_messages += 1
            self._snapshot.received_bytes += size_bytes
            if latency_seconds is not None:
                self._snapshot.latency_samples.append(latency_seconds)
            self._window_count += 1

    def record_dropped(self) -> None:
        with self._lock:
            self._snapshot.dropped_messages += 1

    def record_sequence(self, client_id: int | None, sequence: int | None) -> None:
        if client_id is None or sequence is None:
            return

        with self._lock:
            last_sequence = self._last_sequence_by_client.get(client_id)
            if last_sequence is not None and sequence > last_sequence + 1:
                self._snapshot.lost_messages += sequence - last_sequence - 1
            if last_sequence is None or sequence > last_sequence:
                self._last_sequence_by_client[client_id] = sequence

    def mark_rate_point(self) -> None:
        now = time.time()
        with self._lock:
            elapsed = now - self._last_rate_window
            if elapsed < 1.0:
                return
            rate = self._window_count / elapsed if elapsed > 0 else 0.0
            self._snapshot.messages_per_second.append(
                {"timestamp": now, "messages_per_second": rate}
            )
            self._window_count = 0
            self._last_rate_window = now

    def finish(self) -> MetricsSnapshot:
        with self._lock:
            self._snapshot.finished_at = time.time()
            return self._snapshot

    def snapshot(self) -> MetricsSnapshot:
        with self._lock:
            return MetricsSnapshot(**asdict(self._snapshot))

    @staticmethod
    def save(snapshot: MetricsSnapshot, path: str | Path) -> None:
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("w", encoding="utf-8") as file_handle:
            json.dump(snapshot.to_dict(), file_handle, indent=2, ensure_ascii=True)

    @staticmethod
    def load(path: str | Path) -> dict[str, Any]:
        with Path(path).open("r", encoding="utf-8") as file_handle:
            return json.load(file_handle)
