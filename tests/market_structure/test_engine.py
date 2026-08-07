from __future__ import annotations

from epip.core.event_bus import EventBus
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.engine import MarketStructureEngine
from epip.market_structure.events import (
    BOSDetected,
    CHOCHDetected,
    StructureDetected,
    StructureReset,
    TrendChanged,
)
from epip.market_structure.exceptions import InvalidStructureInputError
from epip.market_structure.models import StructureState, TrendDirection
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _swing(
    symbol: str,
    timeframe: str,
    idx: int,
    price: float,
    classification: SwingClassification,
    pivot: PivotType,
) -> Swing:
    return Swing(
        point=SwingPoint(
            symbol=symbol,
            timeframe=timeframe,
            index=idx,
            timestamp=f"2024-01-01T00:00:{idx:02d}+00:00",
            price=price,
            pivot_type=pivot,
            left_bars=2,
            right_bars=2,
        ),
        classification=classification,
        scope=SwingScope.EXTERNAL,
        distance_from_previous=2,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def _bull_sequence(symbol: str = "EURUSD", timeframe: str = "M1") -> SwingSequence:
    return SwingSequence(
        symbol=symbol,
        timeframe=timeframe,
        swings=(
            _swing(symbol, timeframe, 1, 1.1000, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing(symbol, timeframe, 2, 1.2000, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing(symbol, timeframe, 3, 1.1500, SwingClassification.HIGHER_LOW, PivotType.LOW),
            _swing(symbol, timeframe, 4, 1.2500, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
        ),
    )


def _bear_reversal_sequence() -> SwingSequence:
    return SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing("EURUSD", "M1", 1, 1.1000, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing("EURUSD", "M1", 2, 1.2000, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing("EURUSD", "M1", 3, 1.0500, SwingClassification.LOWER_LOW, PivotType.LOW),
            _swing("EURUSD", "M1", 4, 1.0300, SwingClassification.LOWER_LOW, PivotType.LOW),
        ),
    )


def test_engine_detects_bull_trend_and_bos() -> None:
    bus = EventBus()
    engine = MarketStructureEngine(config=MarketStructureConfig(minimum_swings=4), event_bus=bus)

    snapshot = engine.process_sequence(_bull_sequence())

    assert snapshot.structure.trend.direction == TrendDirection.UPTREND
    assert snapshot.structure.state in (StructureState.ACCUMULATION, StructureState.UPTREND)
    assert snapshot.symbol == "EURUSD"
    assert snapshot.timeframe == "M1"
    assert 0.0 <= snapshot.confidence <= 1.0
    assert snapshot.structure.last_bos is not None
    assert any(isinstance(evt, StructureDetected) for evt in bus.event_history())
    assert any(isinstance(evt, BOSDetected) for evt in bus.event_history())


def test_engine_detects_choch_and_trend_change() -> None:
    bus = EventBus()
    engine = MarketStructureEngine(config=MarketStructureConfig(minimum_swings=4), event_bus=bus)

    engine.process_sequence(_bull_sequence())
    snapshot = engine.process_sequence(_bear_reversal_sequence())

    assert snapshot.structure.last_choch is not None
    assert snapshot.structure.trend.direction == TrendDirection.DOWNTREND
    assert snapshot.structure.state in (StructureState.DISTRIBUTION, StructureState.DOWNTREND)
    assert any(isinstance(evt, CHOCHDetected) for evt in bus.event_history())
    assert any(isinstance(evt, TrendChanged) for evt in bus.event_history())


def test_engine_rejects_edge_case_insufficient_swings() -> None:
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4),
        event_bus=EventBus(),
    )
    short_sequence = SwingSequence(
        symbol="EURUSD", timeframe="M1", swings=_bull_sequence().swings[:3]
    )

    try:
        engine.process_sequence(short_sequence)
        assert False
    except InvalidStructureInputError:
        assert True


def test_engine_handles_multi_symbol_multi_timeframe() -> None:
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4),
        event_bus=EventBus(),
    )

    eur_m1 = _bull_sequence("EURUSD", "M1")
    eur_m5 = _bull_sequence("EURUSD", "M5")
    gbp_m1 = _bull_sequence("GBPUSD", "M1")

    engine.process_sequence(eur_m1)
    engine.process_sequence(eur_m5)
    engine.process_sequence(gbp_m1)

    assert engine.snapshot("EURUSD", "M1") is not None
    assert engine.snapshot("EURUSD", "M5") is not None
    assert engine.snapshot("GBPUSD", "M1") is not None


def test_engine_reset_publishes_reset_event() -> None:
    bus = EventBus()
    engine = MarketStructureEngine(config=MarketStructureConfig(minimum_swings=4), event_bus=bus)

    engine.process_sequence(_bull_sequence())
    engine.reset("EURUSD", "M1")

    assert engine.snapshot("EURUSD", "M1") is None
    assert any(isinstance(evt, StructureReset) for evt in bus.event_history())


def test_engine_metrics_exposed() -> None:
    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4), event_bus=EventBus()
    )
    engine.process_sequence(_bull_sequence())

    metrics = engine.metrics()
    assert metrics.total_processed_swings >= 4
    assert metrics.processing_latency_seconds >= 0.0
    assert metrics.average_detection_time_seconds >= 0.0
