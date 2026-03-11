"""Telemetry is disabled in strict local-only mode."""

from typing import List


def ensure_telemetry_consent() -> None:
    return


def track_usage(orders: List[dict]) -> None:
    return
