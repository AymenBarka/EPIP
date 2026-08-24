"""Immutable metadata envelope around the frozen A07 StrategySignal."""

from __future__ import annotations

from dataclasses import dataclass

from epip.a07.signal import StrategySignal
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import CONTRACT_VERSION, digest, text
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.profile import StrategyProfileIdentity
from epip.strategy_runtime.provenance import FactAdapterIdentity


@dataclass(frozen=True, slots=True)
class StrategySignalEnvelope:
    contract_version: str
    envelope_id: str
    signal: StrategySignal
    evaluation_id: str
    instrument_id: str
    symbol: str
    primary_timeframe: str
    profile_identity: StrategyProfileIdentity
    adapter_identity: FactAdapterIdentity
    provenance_manifest_id: str
    runtime_version: str
    source_set_id: str

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported signal-envelope contract version")
        if type(self.signal) is not StrategySignal:
            raise DataIntegrityError("signal must be a frozen StrategySignal")
        for name in (
            "evaluation_id",
            "instrument_id",
            "symbol",
            "primary_timeframe",
            "provenance_manifest_id",
            "runtime_version",
            "source_set_id",
        ):
            object.__setattr__(self, name, text(getattr(self, name), name))
        if type(self.profile_identity) is not StrategyProfileIdentity:
            raise DataIntegrityError("profile_identity has the wrong type")
        if type(self.adapter_identity) is not FactAdapterIdentity:
            raise DataIntegrityError("adapter_identity has the wrong type")
        if self.envelope_id != digest(self, exclude=frozenset({"envelope_id"})):
            raise DataIntegrityError("envelope_id does not match canonical content")

    @classmethod
    def create(
        cls,
        *,
        signal: StrategySignal,
        context: EvaluationContext,
        adapter_identity: FactAdapterIdentity,
        provenance_manifest_id: str,
        runtime_version: str,
    ) -> StrategySignalEnvelope:
        if signal.evaluation_timestamp != context.evaluation_timestamp:
            raise DataIntegrityError("signal and evaluation context timestamps differ")
        values = (
            signal,
            context.evaluation_id,
            context.instrument_id,
            context.symbol,
            context.primary_timeframe,
            context.profile_identity,
            adapter_identity,
            provenance_manifest_id,
            runtime_version,
            context.source_set_id,
        )
        candidate = object.__new__(cls)
        object.__setattr__(candidate, "envelope_id", "")
        object.__setattr__(candidate, "contract_version", CONTRACT_VERSION)
        for name, value in zip(
            (
                "signal",
                "evaluation_id",
                "instrument_id",
                "symbol",
                "primary_timeframe",
                "profile_identity",
                "adapter_identity",
                "provenance_manifest_id",
                "runtime_version",
                "source_set_id",
            ),
            values,
            strict=True,
        ):
            object.__setattr__(candidate, name, value)
        return cls(CONTRACT_VERSION, digest(candidate, exclude=frozenset({"envelope_id"})), *values)
