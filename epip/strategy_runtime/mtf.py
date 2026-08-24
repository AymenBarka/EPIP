"""Deterministic multi-timeframe coherence boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import (
    CONTRACT_VERSION,
    digest,
    instant,
    text,
    timestamp,
    unique_texts,
)


class TimeframeRole(Enum):
    PRIMARY = "PRIMARY"
    HIGHER = "HIGHER"
    LOWER = "LOWER"


@dataclass(frozen=True, slots=True)
class TimeframeInput:
    timeframe: str
    role: TimeframeRole
    window_open: str
    window_close: str
    as_of_timestamp: str
    closed: bool
    source_refs: tuple[str, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "timeframe", text(self.timeframe, "timeframe"))
        if type(self.role) is not TimeframeRole or type(self.closed) is not bool:
            raise DataIntegrityError("invalid timeframe role or closure state")
        for name in ("window_open", "window_close", "as_of_timestamp"):
            object.__setattr__(self, name, timestamp(getattr(self, name), name))
        if instant(self.window_open) >= instant(self.window_close):
            raise DataIntegrityError("timeframe window must have positive duration")
        if instant(self.window_close) > instant(self.as_of_timestamp):
            raise DataIntegrityError("window_close must not exceed as_of_timestamp")
        if not self.closed:
            raise DataIntegrityError("strategy timeframe inputs must be closed")
        object.__setattr__(
            self, "source_refs", unique_texts(self.source_refs, "source_refs", allow_empty=False)
        )
        object.__setattr__(
            self,
            "provenance_refs",
            unique_texts(self.provenance_refs, "provenance_refs", allow_empty=False),
        )


@dataclass(frozen=True, slots=True)
class MultiTimeframeInputSet:
    contract_version: str
    context_id: str
    primary_timeframe: str
    alignment_timestamp: str
    frames: tuple[TimeframeInput, ...]

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported MTF contract version")
        object.__setattr__(
            self, "primary_timeframe", text(self.primary_timeframe, "primary_timeframe")
        )
        object.__setattr__(
            self, "alignment_timestamp", timestamp(self.alignment_timestamp, "alignment_timestamp")
        )
        if type(self.frames) is not tuple or any(
            type(item) is not TimeframeInput for item in self.frames
        ):
            raise DataIntegrityError("frames must contain TimeframeInput values")
        frames = tuple(sorted(self.frames, key=lambda item: (item.timeframe, item.role.value)))
        if len({item.timeframe for item in frames}) != len(frames):
            raise DataIntegrityError("timeframes must be unique")
        primary = tuple(item for item in frames if item.role is TimeframeRole.PRIMARY)
        if len(primary) != 1 or primary[0].timeframe != self.primary_timeframe:
            raise DataIntegrityError("exactly one matching primary timeframe is required")
        if any(instant(item.window_close) > instant(self.alignment_timestamp) for item in frames):
            raise DataIntegrityError("frame data must not exceed alignment time")
        object.__setattr__(self, "frames", frames)
        expected = digest(self, exclude=frozenset({"context_id"}))
        if self.context_id != expected:
            raise DataIntegrityError("context_id does not match canonical MTF content")

    @classmethod
    def create(
        cls, primary_timeframe: str, alignment_timestamp: str, frames: tuple[TimeframeInput, ...]
    ) -> MultiTimeframeInputSet:
        candidate = object.__new__(cls)
        values = (CONTRACT_VERSION, "", primary_timeframe, alignment_timestamp, frames)
        for name, value in zip(
            (
                "contract_version",
                "context_id",
                "primary_timeframe",
                "alignment_timestamp",
                "frames",
            ),
            values,
            strict=True,
        ):
            object.__setattr__(candidate, name, value)
        identity = digest(candidate, exclude=frozenset({"context_id"}))
        return cls(CONTRACT_VERSION, identity, primary_timeframe, alignment_timestamp, frames)
