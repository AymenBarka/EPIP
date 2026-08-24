from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import EvaluationContext, RuntimeMode


def test_context_is_immutable_hashable_canonical_and_deterministic(
    context: EvaluationContext,
) -> None:
    assert context.evaluation_timestamp.endswith("Z")
    assert hash(context) == hash(replace(context))
    with pytest.raises(FrozenInstanceError):
        context.symbol = "GBPUSD"  # type: ignore[misc]


def test_receipt_time_does_not_change_strategy_identity(context: EvaluationContext) -> None:
    other = EvaluationContext.create(
        instrument_id=context.instrument_id,
        symbol=context.symbol,
        primary_timeframe=context.primary_timeframe,
        evaluation_timestamp=context.evaluation_timestamp,
        event_timestamp=context.event_timestamp,
        receipt_timestamp="2026-08-24T12:31:00Z",
        runtime_mode=RuntimeMode.PAPER,
        profile_identity=context.profile_identity,
        source_set_id=context.source_set_id,
        run_id=context.run_id,
    )
    assert other.evaluation_id == context.evaluation_id


@pytest.mark.parametrize(
    "event,evaluation,receipt",
    [
        ("2026-08-24T12:00:00", "2026-08-24T12:00:00Z", None),
        ("2026-08-24T13:00:00Z", "2026-08-24T12:00:00Z", None),
        ("2026-08-24T12:00:00Z", "2026-08-24T12:00:00Z", "2026-08-24T11:00:00Z"),
    ],
)
def test_invalid_time_semantics_fail_closed(
    context: EvaluationContext, event: str, evaluation: str, receipt: str | None
) -> None:
    with pytest.raises(DataIntegrityError):
        EvaluationContext.create(
            instrument_id=context.instrument_id,
            symbol=context.symbol,
            primary_timeframe=context.primary_timeframe,
            evaluation_timestamp=evaluation,
            event_timestamp=event,
            receipt_timestamp=receipt,
            runtime_mode=context.runtime_mode,
            profile_identity=context.profile_identity,
            source_set_id=context.source_set_id,
            run_id=context.run_id,
        )


def test_runtime_modes_are_exact() -> None:
    assert tuple(item.value for item in RuntimeMode) == (
        "HISTORICAL",
        "BACKTEST",
        "PAPER",
        "MT5_DEMO",
        "LIVE",
    )
