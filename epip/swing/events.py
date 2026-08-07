"""Swing-domain events published by Swing Engine."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.events import BaseEvent
from epip.swing.types import SwingClassification, SwingScope


@dataclass(frozen=True, slots=True, kw_only=True)
class SwingDetected(BaseEvent):
    symbol: str
    timeframe: str
    swing_timestamp: str
    classification: SwingClassification
    scope: SwingScope
    price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class SwingUpdated(BaseEvent):
    symbol: str
    timeframe: str
    swing_timestamp: str
    classification: SwingClassification
    price: float


@dataclass(frozen=True, slots=True, kw_only=True)
class SwingConfirmed(BaseEvent):
    symbol: str
    timeframe: str
    swing_timestamp: str
    classification: SwingClassification


@dataclass(frozen=True, slots=True, kw_only=True)
class SwingRejected(BaseEvent):
    symbol: str
    timeframe: str
    swing_timestamp: str
    reason: str


@dataclass(frozen=True, slots=True, kw_only=True)
class SwingMerged(BaseEvent):
    symbol: str
    timeframe: str
    source_timestamp: str
    target_timestamp: str
    classification: SwingClassification
