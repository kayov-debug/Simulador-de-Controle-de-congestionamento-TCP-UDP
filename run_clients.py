"""Run multiple simulator clients simultaneously."""

from __future__ import annotations

import argparse
import threading
from collections.abc import Callable
from typing import Any

from cliente.tcp_client import TCPClient, TCPClientConfig
from cliente.udp_client import UDPClient, UDPClientConfig
from config import DEFAULT_CLIENTS, DEFAULT_DURATION, DEFAULT_HOST, DEFAULT_PACKET_SIZE, DEFAULT_SEND_INTERVAL, DEFAULT_TCP_PORT, DEFAULT_UDP_PORT


ClientRunner = Callable[[], dict[str, Any]]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start multiple congestion simulator clients")
    parser.add_argument("--protocol", choices=("udp", "tcp"), default="udp")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--clients", type=int, default=DEFAULT_CLIENTS)
    parser.add_argument("--duration", type=float, default=DEFAULT_DURATION)
    parser.add_argument("--packet-size", type=int, default=DEFAULT_PACKET_SIZE)
    parser.add_argument("--send-interval", type=float, default=DEFAULT_SEND_INTERVAL)
    parser.add_argument("--rate-limit", type=float, default=0.0)
    return parser


def _create_runner(protocol: str, host: str, port: int, client_id: int, duration: float, packet_size: int, send_interval: float, rate_limit: float) -> ClientRunner:
    if protocol == "udp":
        client = UDPClient(
            UDPClientConfig(
                host=host,
                port=port,
                client_id=client_id,
                duration=duration,
                packet_size=packet_size,
                send_interval=send_interval,
                rate_limit=rate_limit,
            )
        )
    else:
        client = TCPClient(
            TCPClientConfig(
                host=host,
                port=port,
                client_id=client_id,
                duration=duration,
                packet_size=packet_size,
                send_interval=send_interval,
                rate_limit=rate_limit,
            )
        )
    return client.run


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.port is None:
        args.port = DEFAULT_UDP_PORT if args.protocol == "udp" else DEFAULT_TCP_PORT

    threads: list[threading.Thread] = []
    results: list[dict[str, Any] | None] = [None] * args.clients

    for client_id in range(args.clients):
        runner = _create_runner(
            args.protocol,
            args.host,
            args.port,
            client_id,
            args.duration,
            args.packet_size,
            args.send_interval,
            args.rate_limit,
        )

        def execute(index: int, run: ClientRunner) -> None:
            results[index] = run()

        thread = threading.Thread(target=execute, args=(client_id, runner), daemon=True)
        threads.append(thread)
        thread.start()

    for thread in threads:
        thread.join()

    total_sent = sum(result["sent_messages"] for result in results if result is not None)
    total_bytes = sum(result["sent_bytes"] for result in results if result is not None)
    print("\nClients finished")
    print(f"Total messages sent: {total_sent}")
    print(f"Total bytes sent: {total_bytes}")


if __name__ == "__main__":
    main()
