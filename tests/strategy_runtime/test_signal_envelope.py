from dataclasses import replace

import pytest

from epip.a07.signal import StrategySignal
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import (
    EvaluationContext,
    FactAdapterIdentity,
    StrategySignalEnvelope,
)


def test_envelope_preserves_signal_without_geometry_duplicates(
    signal: StrategySignal,
    context: EvaluationContext,
    adapter_identity: FactAdapterIdentity,
) -> None:
    envelope = StrategySignalEnvelope.create(
        signal=signal,
        context=context,
        adapter_identity=adapter_identity,
        provenance_manifest_id="manifest",
        runtime_version="1",
    )
    assert envelope.signal is signal
    assert not {"direction", "entry", "stop", "target", "rr", "confidence", "expires_at"} & {
        field for field in envelope.__slots__
    }
    with pytest.raises(DataIntegrityError):
        replace(envelope, envelope_id="0" * 64)


def test_envelope_rejects_timestamp_mismatch(
    signal: StrategySignal,
    context: EvaluationContext,
    adapter_identity: FactAdapterIdentity,
) -> None:
    other = EvaluationContext.create(
        instrument_id=context.instrument_id,
        symbol=context.symbol,
        primary_timeframe=context.primary_timeframe,
        evaluation_timestamp="2026-08-24T12:30:16.000000Z",
        event_timestamp=context.event_timestamp,
        receipt_timestamp=context.receipt_timestamp,
        runtime_mode=context.runtime_mode,
        profile_identity=context.profile_identity,
        source_set_id=context.source_set_id,
        run_id=context.run_id,
    )
    with pytest.raises(DataIntegrityError):
        StrategySignalEnvelope.create(
            signal=signal,
            context=other,
            adapter_identity=adapter_identity,
            provenance_manifest_id="manifest",
            runtime_version="1",
        )
