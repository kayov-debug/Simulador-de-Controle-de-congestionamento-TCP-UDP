"""TCP server for congestion simulation."""

from __future__ import annotations

import json
import random
import socket
import struct
import threading
import time
from dataclasses import dataclass
from typing import Any

from config import DEFAULT_BUFFER_SIZE, DEFAULT_METRICS_FILE, DEFAULT_REPORT_INTERVAL
from utilitarios.metrics import MetricsCollector
from utilitarios.rate_limiter import RateLimiter


@dataclass
class TCPServerConfig:
    host: str
    port: int
    rate_limit: float = 0.0
    loss_rate: float = 0.0
    buffer_size: int = DEFAULT_BUFFER_SIZE
    report_interval: float = DEFAULT_REPORT_INTERVAL
    metrics_file: str = str(DEFAULT_METRICS_FILE)
    duration: float | None = None


class TCPServer:
    def __init__(self, config: TCPServerConfig) -> None:
        self.config = config
        self.metrics = MetricsCollector()
        self.rate_limiter = RateLimiter(config.rate_limit) if config.rate_limit > 0 else None
        self._stop_event = threading.Event()

    @staticmethod
    def _recv_exact(connection: socket.socket, size: int) -> bytes | None:
        chunks = bytearray()
        while len(chunks) < size:
            chunk = connection.recv(size - len(chunks))
            if not chunk:
                return None
            chunks.extend(chunk)
        return bytes(chunks)

    def _handle_client(self, connection: socket.socket, address: tuple[str, int]) -> None:
        with connection:
            while not self._stop_event.is_set():
                length_bytes = self._recv_exact(connection, 4)
                if not length_bytes:
                    return
                message_length = struct.unpack("!I", length_bytes)[0]
                payload = self._recv_exact(connection, message_length)
                if payload is None:
                    return

                if self.rate_limiter is not None and not self.rate_limiter.allow():
                    self.metrics.record_dropped()
                    continue

                if self.config.loss_rate > 0 and random.random() < self.config.loss_rate:
                    continue

                try:
                    data = json.loads(payload.decode("utf-8"))
                except (UnicodeDecodeError, json.JSONDecodeError):
                    data = {}

                client_id = data.get("client_id")
                sequence = data.get("sequence")
                if isinstance(client_id, int) and isinstance(sequence, int):
                    self.metrics.record_sequence(client_id, sequence)

                sent_at = data.get("sent_at")
                latency = None
                if isinstance(sent_at, (int, float)):
                    latency = time.time() - float(sent_at)
                self.metrics.record_received(len(payload) + 4, latency)
                self.metrics.mark_rate_point()

    def run(self) -> dict[str, Any]:
        start_time = time.time()
        deadline = None if self.config.duration is None else start_time + self.config.duration
        last_report = time.time()

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server_socket:
            server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server_socket.bind((self.config.host, self.config.port))
            server_socket.listen()
            server_socket.settimeout(0.5)
            print(f"TCP server listening on {self.config.host}:{self.config.port}")

            while True:
                if deadline is not None and time.time() >= deadline:
                    break
                try:
                    connection, address = server_socket.accept()
                except socket.timeout:
                    self.metrics.mark_rate_point()
                    if time.time() - last_report >= self.config.report_interval:
                        self._print_report()
                        last_report = time.time()
                    continue

                thread = threading.Thread(
                    target=self._handle_client,
                    args=(connection, address),
                    daemon=True,
                )
                thread.start()

        self._stop_event.set()
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
        print("\nTCP server finished")
        print(f"Duration: {summary['duration']:.2f}s")
        print(f"Received messages: {summary['received_messages']}")
        print(f"Dropped messages: {summary['dropped_messages']}")
        print(f"Lost messages: {summary['lost_messages']}")
        print(f"Packet loss rate (observed): {summary['loss_rate_percent']:.2f}%")
        print(f"Average throughput: {summary['throughput_mbps']:.3f} Mbps")
        print(f"Average latency: {summary['latency_avg_ms']:.2f} ms")
