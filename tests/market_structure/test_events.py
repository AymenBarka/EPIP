from __future__ import annotations

from epip.market_structure.events import (
    BOSDetected,
    CHOCHDetected,
    RangeDetected,
    StructureDetected,
    StructureReset,
    TrendChanged,
)
from epip.market_structure.models import StructureState, TrendDirection


def test_events_instantiation() -> None:
    detected = StructureDetected(
        id="s-1",
        timestamp="2024-01-01T00:00:00+00:00",
        symbol="EURUSD",
        timeframe="M1",
        trend=TrendDirection.UPTREND,
        state=StructureState.UPTREND,
    )
    bos = BOSDetected(
        id="b-1",
        timestamp="2024-01-01T00:00:01+00:00",
        symbol="EURUSD",
        timeframe="M1",
        direction=TrendDirection.UPTREND,
        break_price=1.2,
        reference_price=1.1,
    )
    choch = CHOCHDetected(
        id="c-1",
        timestamp="2024-01-01T00:00:02+00:00",
        symbol="EURUSD",
        timeframe="M1",
        previous_trend=TrendDirection.UPTREND,
        new_trend=TrendDirection.DOWNTREND,
    )
    trend_changed = TrendChanged(
        id="t-1",
        timestamp="2024-01-01T00:00:03+00:00",
        symbol="EURUSD",
        timeframe="M1",
        previous_trend=TrendDirection.UNKNOWN,
        new_trend=TrendDirection.UPTREND,
    )
    range_detected = RangeDetected(
        id="r-1",
        timestamp="2024-01-01T00:00:04+00:00",
        symbol="EURUSD",
        timeframe="M1",
        range_high=1.2,
        range_low=1.0,
        touches_high=2,
        touches_low=2,
    )
    reset = StructureReset(
        id="x-1",
        timestamp="2024-01-01T00:00:05+00:00",
        symbol="EURUSD",
        timeframe="M1",
    )

    assert detected.state == StructureState.UPTREND
    assert detected.event_id == "s-1"
    assert detected.engine_version == "EPIP-007"
    assert detected.source == "market-structure-engine"
    assert bos.break_price > bos.reference_price
    assert choch.new_trend == TrendDirection.DOWNTREND
    assert trend_changed.previous_trend == TrendDirection.UNKNOWN
    assert range_detected.touches_high == 2
    assert reset.symbol == "EURUSD"
