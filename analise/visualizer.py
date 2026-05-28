"""Visualize collected metrics."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt


def load_metrics(path: str | Path) -> dict[str, Any]:
    with Path(path).open("r", encoding="utf-8") as file_handle:
        return json.load(file_handle)


def plot_metrics(metrics: dict[str, Any], output_dir: str | Path = "results") -> None:
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    figure, axes = plt.subplots(3, 1, figsize=(10, 11), constrained_layout=True)

    rate_points = metrics.get("messages_per_second", [])
    if rate_points:
        x_values = list(range(1, len(rate_points) + 1))
        y_values = [entry.get("messages_per_second", 0) for entry in rate_points]
        axes[0].plot(x_values, y_values, marker="o", linewidth=2)
        axes[0].set_title("Messages per second")
        axes[0].set_xlabel("Sample")
        axes[0].set_ylabel("Messages/s")
        axes[0].grid(True, alpha=0.3)
    else:
        axes[0].text(0.5, 0.5, "No rate samples available", ha="center", va="center")
        axes[0].set_axis_off()

    latency_samples = metrics.get("latency_samples", [])
    if latency_samples:
        axes[1].hist([value * 1000 for value in latency_samples], bins=20, color="#3b82f6")
        axes[1].set_title("Latency distribution")
        axes[1].set_xlabel("Latency (ms)")
        axes[1].set_ylabel("Frequency")
    else:
        axes[1].text(0.5, 0.5, "No latency samples available", ha="center", va="center")
        axes[1].set_axis_off()

    received = int(metrics.get("received_messages", 0))
    dropped = int(metrics.get("dropped_messages", 0))
    lost = int(metrics.get("lost_messages", 0))
    labels = ["Received", "Dropped", "Lost"]
    values = [received, dropped, lost]
    colors = ["#10b981", "#f59e0b", "#ef4444"]
    axes[2].bar(labels, values, color=colors)
    axes[2].set_title("Packet outcome")
    axes[2].set_ylabel("Count")
    axes[2].grid(True, axis="y", alpha=0.3)
    loss_rate = metrics.get("loss_rate_percent", 0.0)
    drop_rate = metrics.get("drop_rate_percent", 0.0)
    axes[2].text(0.02, 0.95, f"Loss: {loss_rate:.2f}% | Drop: {drop_rate:.2f}%", transform=axes[2].transAxes, va="top")

    figure.suptitle("Congestion Simulator Metrics", fontsize=14)
    figure.savefig(output_path / "metrics.png", dpi=150)
    plt.close(figure)


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Plot simulator metrics")
    parser.add_argument("metrics_file", help="Path to the metrics JSON file")
    parser.add_argument("--output-dir", default="results", help="Directory for generated plots")
    args = parser.parse_args()

    metrics = load_metrics(args.metrics_file)
    plot_metrics(metrics, args.output_dir)
    print(f"Plot saved to {Path(args.output_dir) / 'metrics.png'}")


if __name__ == "__main__":
    main()
