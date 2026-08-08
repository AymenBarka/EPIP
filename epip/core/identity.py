"""Clock and identity services used by deterministic EPIP workflows."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import RLock
from typing import Protocol
from uuid import uuid4


class ClockProtocol(Protocol):
    """Source of explicit UTC timestamps."""

    def now(self) -> str: ...


class IdGeneratorProtocol(Protocol):
    """Source of technical identifiers."""

    def generate(self, namespace: str, *parts: object) -> str: ...


class SystemClock:
    """Production clock backed by the system UTC clock."""

    def now(self) -> str:
        return datetime.now(UTC).isoformat()


class DeterministicClock:
    """Thread-safe clock controlled explicitly by tests and replay."""

    def __init__(self, current: str = "1970-01-01T00:00:00+00:00") -> None:
        self._current = self._parse(current)
        self._lock = RLock()

    def now(self) -> str:
        with self._lock:
            return self._current.isoformat()

    def set(self, timestamp: str) -> None:
        with self._lock:
            self._current = self._parse(timestamp)

    def advance(self, delta: timedelta) -> str:
        with self._lock:
            self._current += delta
            return self._current.isoformat()

    @staticmethod
    def _parse(timestamp: str) -> datetime:
        value = datetime.fromisoformat(timestamp)
        if value.tzinfo is None:
            value = value.replace(tzinfo=UTC)
        return value.astimezone(UTC)


class SystemIdGenerator:
    """Backward-compatible generator for production technical IDs."""

    def generate(self, namespace: str, *parts: object) -> str:
        del namespace, parts
        return uuid4().hex


class DeterministicIdGenerator:
    """Generate a reproducible sequence of opaque hexadecimal IDs."""

    def __init__(self, seed: str = "epip") -> None:
        self._seed = seed
        self._counter = 0
        self._lock = RLock()

    def generate(self, namespace: str, *parts: object) -> str:
        with self._lock:
            counter = self._counter
            self._counter += 1
        material = "\x1f".join(
            (self._seed, namespace, *(str(part) for part in parts), str(counter))
        )
        return sha256(material.encode("utf-8")).hexdigest()[:32]

    def reset(self) -> None:
        with self._lock:
            self._counter = 0


def resolve_clock(clock: ClockProtocol | None) -> ClockProtocol:
    return clock if clock is not None else SystemClock()


def resolve_id_generator(generator: IdGeneratorProtocol | None) -> IdGeneratorProtocol:
    return generator if generator is not None else SystemIdGenerator()
