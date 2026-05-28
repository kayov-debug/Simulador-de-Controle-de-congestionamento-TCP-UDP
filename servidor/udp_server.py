"""UDP server for congestion simulation."""

from __future__ import annotations

import json
import random
import socket
import time
from dataclasses import dataclass
from typing import Any

from config import DEFAULT_BUFFER_SIZE, DEFAULT_METRICS_FILE, DEFAULT_REPORT_INTERVAL
from utilitarios.metrics import MetricsCollector
from utilitarios.rate_limiter import RateLimiter


@dataclass
class UDPServerConfig:
    host: str
    port: int
    rate_limit: float = 0.0
    loss_rate: float = 0.0
    buffer_size: int = DEFAULT_BUFFER_SIZE
    report_interval: float = DEFAULT_REPORT_INTERVAL
    metrics_file: str = str(DEFAULT_METRICS_FILE)
    duration: float | None = None


class UDPServer:
    def __init__(self, config: UDPServerConfig) -> None:
        self.config = config
        self.metrics = MetricsCollector()
        self.rate_limiter = RateLimiter(config.rate_limit) if config.rate_limit > 0 else None
        self._socket: socket.socket | None = None
        self._started_at = 0.0

    def _decode_message(self, data: bytes) -> dict[str, Any]:
        try:
            return json.loads(data.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError):
            return {}

    def run(self) -> dict[str, Any]:
        self._started_at = time.time()
        deadline = None if self.config.duration is None else self._started_at + self.config.duration
        last_report = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as udp_socket:
            self._socket = udp_socket
            udp_socket.bind((self.config.host, self.config.port))
            udp_socket.settimeout(0.5)
            print(f"UDP server listening on {self.config.host}:{self.config.port}")

            while True:
                if deadline is not None and time.time() >= deadline:
                    break

                try:
                    data, address = udp_socket.recvfrom(self.config.buffer_size)
                except socket.timeout:
                    self.metrics.mark_rate_point()
                    if time.time() - last_report >= self.config.report_interval:
                        self._print_report()
                        last_report = time.time()
                    continue

                if self.rate_limiter is not None and not self.rate_limiter.allow():
                    self.metrics.record_dropped()
                    continue

                if self.config.loss_rate > 0 and random.random() < self.config.loss_rate:
                    continue

                payload = self._decode_message(data)
                client_id = payload.get("client_id")
                sequence = payload.get("sequence")
                if isinstance(client_id, int) and isinstance(sequence, int):
                    self.metrics.record_sequence(client_id, sequence)
                sent_at = payload.get("sent_at")
                latency = None
                if isinstance(sent_at, (int, float)):
                    latency = time.time() - float(sent_at)
                self.metrics.record_received(len(data), latency)
                self.metrics.mark_rate_point()

                if time.time() - last_report >= self.config.report_interval:
                    self._print_report()
                    last_report = time.time()

        snapshot = self.metrics.finish()
        self.metrics.save(snapshot, self.config.metrics_file)
        summary = snapshot.to_dict()
        self._print_summary(summary)
        return summary

    def _print_report(self) -> None:
        snapshot = self.metrics.snapshot()
        print(
            f"received={snapshot.received_messages} dropped={snapshot.dropped_messages} "
            f"throughput={snapshot.throughput_mbps:.3f} Mbps latency={snapshot.latency_avg_ms:.2f} ms"
        )

    @staticmethod
    def _print_summary(summary: dict[str, Any]) -> None:
        print("\nUDP server finished")
        print(f"Duration: {summary['duration']:.2f}s")
        print(f"Received messages: {summary['received_messages']}")
        print(f"Dropped messages: {summary['dropped_messages']}")
        print(f"Lost messages: {summary['lost_messages']}")
        print(f"Packet loss rate (observed): {summary['loss_rate_percent']:.2f}%")
        print(f"Average throughput: {summary['throughput_mbps']:.3f} Mbps")
        print(f"Average latency: {summary['latency_avg_ms']:.2f} ms")
