"""Deterministic evaluation-boundary contracts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import (
    CONTRACT_VERSION,
    digest,
    instant,
    optional_text,
    text,
    timestamp,
)
from epip.strategy_runtime.profile import StrategyProfileIdentity


class RuntimeMode(Enum):
    HISTORICAL = "HISTORICAL"
    BACKTEST = "BACKTEST"
    PAPER = "PAPER"
    MT5_DEMO = "MT5_DEMO"
    LIVE = "LIVE"


@dataclass(frozen=True, slots=True)
class EvaluationContext:
    contract_version: str
    evaluation_id: str
    instrument_id: str
    symbol: str
    primary_timeframe: str
    evaluation_timestamp: str
    event_timestamp: str
    receipt_timestamp: str | None
    runtime_mode: RuntimeMode
    profile_identity: StrategyProfileIdentity
    source_set_id: str
    run_id: str
    correlation_id: str | None = None

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported evaluation contract version")
        for name in ("instrument_id", "symbol", "primary_timeframe", "source_set_id", "run_id"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        object.__setattr__(
            self, "correlation_id", optional_text(self.correlation_id, "correlation_id")
        )
        evaluation = timestamp(self.evaluation_timestamp, "evaluation_timestamp")
        event = timestamp(self.event_timestamp, "event_timestamp")
        receipt = (
            None
            if self.receipt_timestamp is None
            else timestamp(self.receipt_timestamp, "receipt_timestamp")
        )
        if instant(event) > instant(evaluation):
            raise DataIntegrityError("event_timestamp must not exceed evaluation_timestamp")
        if receipt is not None and instant(receipt) < instant(event):
            raise DataIntegrityError("receipt_timestamp must not precede event_timestamp")
        if type(self.runtime_mode) is not RuntimeMode:
            raise DataIntegrityError("runtime_mode must be a RuntimeMode")
        if type(self.profile_identity) is not StrategyProfileIdentity:
            raise DataIntegrityError("profile_identity must be a StrategyProfileIdentity")
        object.__setattr__(self, "evaluation_timestamp", evaluation)
        object.__setattr__(self, "event_timestamp", event)
        object.__setattr__(self, "receipt_timestamp", receipt)
        expected = digest(
            self,
            exclude=frozenset({"evaluation_id", "receipt_timestamp", "correlation_id"}),
        )
        if self.evaluation_id != expected:
            raise DataIntegrityError("evaluation_id does not match canonical semantic content")

    @classmethod
    def create(
        cls,
        *,
        instrument_id: str,
        symbol: str,
        primary_timeframe: str,
        evaluation_timestamp: str,
        event_timestamp: str,
        receipt_timestamp: str | None,
        runtime_mode: RuntimeMode,
        profile_identity: StrategyProfileIdentity,
        source_set_id: str,
        run_id: str,
        correlation_id: str | None = None,
    ) -> EvaluationContext:
        candidate = object.__new__(cls)
        values = {
            "contract_version": CONTRACT_VERSION,
            "evaluation_id": "",
            "instrument_id": instrument_id,
            "symbol": symbol,
            "primary_timeframe": primary_timeframe,
            "evaluation_timestamp": timestamp(evaluation_timestamp, "evaluation_timestamp"),
            "event_timestamp": timestamp(event_timestamp, "event_timestamp"),
            "receipt_timestamp": receipt_timestamp,
            "runtime_mode": runtime_mode,
            "profile_identity": profile_identity,
            "source_set_id": source_set_id,
            "run_id": run_id,
            "correlation_id": correlation_id,
        }
        for name, value in values.items():
            object.__setattr__(candidate, name, value)
        identity = digest(
            candidate,
            exclude=frozenset({"evaluation_id", "receipt_timestamp", "correlation_id"}),
        )
        return cls(
            contract_version=CONTRACT_VERSION,
            evaluation_id=identity,
            instrument_id=instrument_id,
            symbol=symbol,
            primary_timeframe=primary_timeframe,
            evaluation_timestamp=evaluation_timestamp,
            event_timestamp=event_timestamp,
            receipt_timestamp=receipt_timestamp,
            runtime_mode=runtime_mode,
            profile_identity=profile_identity,
            source_set_id=source_set_id,
            run_id=run_id,
            correlation_id=correlation_id,
        )
