"""Run the simulator server."""

from __future__ import annotations

import argparse

from config import DEFAULT_HOST, DEFAULT_METRICS_FILE, DEFAULT_RATE_LIMIT, DEFAULT_REPORT_INTERVAL, DEFAULT_TCP_PORT, DEFAULT_UDP_PORT
from servidor.tcp_server import TCPServer, TCPServerConfig
from servidor.udp_server import UDPServer, UDPServerConfig


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Start the congestion simulator server")
    parser.add_argument("--protocol", choices=("udp", "tcp"), default="udp")
    parser.add_argument("--host", default=DEFAULT_HOST)
    parser.add_argument("--port", type=int, default=None)
    parser.add_argument("--rate-limit", type=float, default=DEFAULT_RATE_LIMIT)
    parser.add_argument("--loss-rate", type=float, default=0.0, help="Packet loss probability between 0 and 1")
    parser.add_argument("--duration", type=float, default=None)
    parser.add_argument("--report-interval", type=float, default=DEFAULT_REPORT_INTERVAL)
    parser.add_argument("--metrics-file", default=str(DEFAULT_METRICS_FILE))
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    if args.port is None:
        args.port = DEFAULT_UDP_PORT if args.protocol == "udp" else DEFAULT_TCP_PORT

    if args.protocol == "udp":
        server = UDPServer(
            UDPServerConfig(
                host=args.host,
                port=args.port,
                rate_limit=args.rate_limit,
                loss_rate=args.loss_rate,
                report_interval=args.report_interval,
                metrics_file=args.metrics_file,
                duration=args.duration,
            )
        )
    else:
        server = TCPServer(
            TCPServerConfig(
                host=args.host,
                port=args.port,
                rate_limit=args.rate_limit,
                loss_rate=args.loss_rate,
                report_interval=args.report_interval,
                metrics_file=args.metrics_file,
                duration=args.duration,
            )
        )

    server.run()


if __name__ == "__main__":
    main()
