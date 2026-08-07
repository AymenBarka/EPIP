"""Replay engine state definitions."""

from __future__ import annotations

from enum import Enum


class ReplayState(str, Enum):
    """Lifecycle states for a replay session."""

    CREATED = "created"
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    STOPPED = "stopped"
    FINISHED = "finished"
    ERROR = "error"
