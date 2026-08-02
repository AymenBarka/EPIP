"""Replay-specific domain events."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.events import BaseEvent


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplayStarted(BaseEvent):
    session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplayPaused(BaseEvent):
    session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplayResumed(BaseEvent):
    session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ReplayFinished(BaseEvent):
    session_id: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CandleLoaded(BaseEvent):
    symbol: str
    timeframe: str
    candle_timestamp: str


@dataclass(frozen=True, slots=True, kw_only=True)
class CandleProcessed(BaseEvent):
    symbol: str
    timeframe: str
    candle_timestamp: str


@dataclass(frozen=True, slots=True, kw_only=True)
class ContextUpdated(BaseEvent):
    symbol: str
    timeframe: str
    context_timestamp: str


@dataclass(frozen=True, slots=True, kw_only=True)
class FeatureUpdated(BaseEvent):
    symbol: str
    timeframe: str
    feature_timestamp: str
    feature_count: int
