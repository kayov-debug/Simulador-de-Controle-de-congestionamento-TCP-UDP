"""TCP client for congestion simulation."""

from __future__ import annotations

import json
import socket
import struct
import time
from dataclasses import dataclass
from typing import Any

from utilitarios.metrics import MetricsCollector
from utilitarios.rate_limiter import RateLimiter


@dataclass
class TCPClientConfig:
    host: str
    port: int
    client_id: int
    duration: float
    packet_size: int = 1024
    send_interval: float = 0.05
    rate_limit: float = 0.0


class TCPClient:
    def __init__(self, config: TCPClientConfig) -> None:
        self.config = config
        self.metrics = MetricsCollector()
        self.rate_limiter = RateLimiter(config.rate_limit) if config.rate_limit > 0 else None

    def _build_packet(self, sequence: int) -> bytes:
        payload = {
            "client_id": self.config.client_id,
            "sequence": sequence,
            "sent_at": time.time(),
            "payload": "x" * max(self.config.packet_size - 128, 0),
        }
        raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
        return raw

    def run(self) -> dict[str, Any]:
        deadline = time.time() + self.config.duration
        sequence = 0

        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as tcp_socket:
            tcp_socket.connect((self.config.host, self.config.port))
            while time.time() < deadline:
                if self.rate_limiter is not None and not self.rate_limiter.allow():
                    time.sleep(self.rate_limiter.wait_time())
                    continue

                packet = self._build_packet(sequence)
                message = struct.pack("!I", len(packet)) + packet
                tcp_socket.sendall(message)
                self.metrics.record_sent(len(message))
                sequence += 1
                if self.config.send_interval > 0:
                    time.sleep(self.config.send_interval)

        snapshot = self.metrics.finish()
        return snapshot.to_dict()
