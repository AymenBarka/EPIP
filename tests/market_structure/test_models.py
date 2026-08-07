from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import Any, cast

from epip.market_structure.models import (
    BreakOfStructure,
    ChangeOfCharacter,
    MarketStructure,
    MarketStructureSnapshot,
    Range,
    StructureQuality,
    StructureState,
    StructureStatistics,
    Trend,
    TrendDirection,
)
from epip.swing.models import Swing, SwingPoint
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _swing(idx: int, price: float, pivot: PivotType) -> Swing:
    return Swing(
        point=SwingPoint(
            symbol="EURUSD",
            timeframe="M1",
            index=idx,
            timestamp=f"2024-01-01T00:00:{idx:02d}+00:00",
            price=price,
            pivot_type=pivot,
            left_bars=2,
            right_bars=2,
        ),
        classification=(
            SwingClassification.HIGHER_HIGH
            if pivot == PivotType.HIGH
            else SwingClassification.HIGHER_LOW
        ),
        scope=SwingScope.EXTERNAL,
        distance_from_previous=2,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def test_models_are_immutable_and_constructible() -> None:
    origin = _swing(9, 1.09, PivotType.LOW)
    destination = _swing(10, 1.2, PivotType.HIGH)
    trend = Trend(
        direction=TrendDirection.UPTREND,
        since_index=10,
        since_timestamp="2024-01-01T00:00:10+00:00",
        last_updated_timestamp="2024-01-01T00:00:10+00:00",
        origin_swing=origin,
        destination_swing=destination,
    )
    bos = BreakOfStructure(
        symbol="EURUSD",
        timeframe="M1",
        timestamp="2024-01-01T00:00:11+00:00",
        direction=TrendDirection.UPTREND,
        reference_price=1.1,
        break_price=1.2,
        swing_index=11,
        confirmed=True,
        origin_swing=origin,
        destination_swing=destination,
    )
    choch = ChangeOfCharacter(
        symbol="EURUSD",
        timeframe="M1",
        timestamp="2024-01-01T00:00:12+00:00",
        previous_trend=TrendDirection.UPTREND,
        new_trend=TrendDirection.DOWNTREND,
        trigger_price=1.05,
        swing_index=12,
        origin_swing=destination,
        destination_swing=origin,
    )
    range_regime = Range(
        symbol="EURUSD",
        timeframe="M1",
        start_index=1,
        end_index=12,
        range_high=1.2,
        range_low=1.0,
        touches_high=3,
        touches_low=3,
        active=True,
    )
    structure = MarketStructure(
        symbol="EURUSD",
        timeframe="M1",
        trend=trend,
        state=StructureState.UPTREND,
        last_bos=bos,
        last_choch=choch,
        active_range=range_regime,
        processed_swings=20,
        confidence=0.84,
        quality=StructureQuality.VERY_HIGH,
    )
    snapshot = MarketStructureSnapshot(
        timestamp="2024-01-01T00:00:12+00:00",
        structure=structure,
    )
    stats = StructureStatistics(
        number_of_bos=1,
        number_of_choch=1,
        trend_changes=1,
        ranges=1,
        processed_swings=20,
        processing_time_seconds=0.5,
    )

    assert snapshot.structure.symbol == "EURUSD"
    assert snapshot.symbol == "EURUSD"
    assert 0.0 <= snapshot.confidence <= 1.0
    assert snapshot.quality == StructureQuality.VERY_HIGH
    assert stats.number_of_bos == 1

    try:
        mutable_ref = cast(Any, trend)
        mutable_ref.direction = TrendDirection.DOWNTREND
        assert False
    except FrozenInstanceError:
        assert True
