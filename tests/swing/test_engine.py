from __future__ import annotations

from collections.abc import Iterable

from epip.core.candle import Candle
from epip.core.event_bus import EventBus
from epip.swing.config import SwingConfig
from epip.swing.engine import SwingEngine
from epip.swing.events import SwingConfirmed, SwingDetected, SwingUpdated
from epip.swing.pivot_detector import (
    ATRAdaptiveStrategy,
    FractalStrategy,
    HybridStrategy,
    ZigZagStrategy,
)
from epip.swing.types import SwingClassification


def _candle(symbol: str, timeframe: str, idx: int, close: float, spread: float = 0.0008) -> Candle:
    high = close + spread
    low = close - spread
    return Candle(
        timestamp=f"2024-01-01T00:{idx // 60:02d}:{idx % 60:02d}+00:00",
        symbol=symbol,
        timeframe=timeframe,
        open=close - (spread / 4.0),
        high=high,
        low=low,
        close=close,
        volume=1000.0 + float(idx),
    )


def _series(symbol: str, timeframe: str, closes: Iterable[float]) -> list[Candle]:
    return [_candle(symbol, timeframe, idx, close) for idx, close in enumerate(closes)]


def test_engine_handles_flat_market() -> None:
    candles = _series("EURUSD", "M1", [1.1000] * 40)
    engine = SwingEngine(config=SwingConfig(left_bars=2, right_bars=2), event_bus=EventBus())

    metrics = engine.run(candles)

    assert metrics.swings_count >= 0
    assert metrics.elapsed_time_seconds >= 0.0


def test_engine_detects_bullish_hh_hl() -> None:
    closes = [1.1000, 1.1005, 1.1002, 1.1010, 1.1007, 1.1015, 1.1011, 1.1020, 1.1016, 1.1025]
    candles = _series("EURUSD", "M1", closes)
    engine = SwingEngine(
        config=SwingConfig(
            left_bars=1,
            right_bars=1,
            minimum_distance=1,
            minimum_price_move=0.00001,
        ),
        event_bus=EventBus(),
    )

    metrics = engine.run(candles)

    assert metrics.swings_count > 0
    assert metrics.higher_high_count >= 1


def test_engine_detects_bearish_lh_ll() -> None:
    closes = [1.1020, 1.1015, 1.1018, 1.1010, 1.1012, 1.1005, 1.1008, 1.1000, 1.1002, 1.0995]
    candles = _series("EURUSD", "M1", closes)
    engine = SwingEngine(
        config=SwingConfig(left_bars=1, right_bars=1, minimum_price_move=0.00001),
        event_bus=EventBus(),
    )

    metrics = engine.run(candles)

    assert metrics.swings_count > 0
    assert metrics.lower_low_count >= 1


def test_engine_handles_noisy_market_and_gaps() -> None:
    closes = [
        1.1000,
        1.1009,
        1.0998,
        1.1012,
        1.1001,
        1.1028,
        1.1010,
        1.0997,
        1.1035,
        1.1022,
        1.0988,
        1.1005,
    ]
    candles = _series("EURUSD", "M1", closes)
    engine = SwingEngine(
        config=SwingConfig(left_bars=1, right_bars=1, minimum_distance=1),
        event_bus=EventBus(),
    )

    metrics = engine.run(candles)

    assert metrics.swings_count >= 2


def test_engine_detects_equal_highs_and_lows() -> None:
    closes = [1.1000, 1.1010, 1.1004, 1.1010, 1.1003, 1.1010, 1.1002, 1.1010, 1.1001]
    event_bus = EventBus()
    engine = SwingEngine(
        config=SwingConfig(
            left_bars=1,
            right_bars=1,
            equal_high_threshold=0.0002,
            equal_low_threshold=0.0002,
        ),
        event_bus=event_bus,
    )

    metrics = engine.run(_series("EURUSD", "M1", closes))

    assert metrics.equal_high_count >= 1 or metrics.equal_low_count >= 1
    assert any(isinstance(evt, SwingUpdated) for evt in event_bus.event_history())


def test_engine_edge_case_short_stream() -> None:
    candles = _series("EURUSD", "M1", [1.1000, 1.1002])
    engine = SwingEngine(config=SwingConfig(left_bars=2, right_bars=2), event_bus=EventBus())

    metrics = engine.run(candles)

    assert metrics.swings_count == 0


def test_engine_supports_multi_symbol_multi_timeframe() -> None:
    event_bus = EventBus()
    engine = SwingEngine(config=SwingConfig(left_bars=1, right_bars=1), event_bus=event_bus)

    streams = [
        _series("EURUSD", "M1", [1.1000, 1.1010, 1.1004, 1.1012, 1.1005]),
        _series("EURUSD", "M5", [1.2000, 1.2010, 1.2002, 1.2012, 1.2003]),
        _series("GBPUSD", "M1", [1.3000, 1.2990, 1.2995, 1.2988, 1.2991]),
    ]

    for idx in range(5):
        for stream in streams:
            engine.process_candle(stream[idx])

    seq_eur_m1 = engine.sequence("EURUSD", "M1")
    seq_eur_m5 = engine.sequence("EURUSD", "M5")
    seq_gbp_m1 = engine.sequence("GBPUSD", "M1")

    assert len(seq_eur_m1) > 0
    assert len(seq_eur_m5) > 0
    assert len(seq_gbp_m1) > 0
    history = event_bus.event_history()
    assert any(isinstance(evt, SwingDetected) for evt in history)
    assert any(isinstance(evt, SwingConfirmed) for evt in history)


def test_filters_can_reduce_micro_swings() -> None:
    candles = _series(
        "EURUSD",
        "M1",
        [1.1000, 1.1001, 1.1000, 1.1001, 1.1000, 1.1001, 1.1000, 1.1001],
    )

    loose = SwingEngine(config=SwingConfig(left_bars=1, right_bars=1), event_bus=EventBus())
    strict = SwingEngine(
        config=SwingConfig(
            left_bars=1,
            right_bars=1,
            minimum_distance=2,
            minimum_price_move=0.0002,
        ),
        event_bus=EventBus(),
    )

    loose_metrics = loose.run(candles)
    strict_metrics = strict.run(candles)

    assert strict_metrics.swings_count <= loose_metrics.swings_count


def test_strategy_placeholders_are_explicit() -> None:
    config = SwingConfig()
    sample = _candle("EURUSD", "M1", 0, 1.1)

    for strategy in (
        FractalStrategy(config),
        ATRAdaptiveStrategy(config),
        ZigZagStrategy(config),
        HybridStrategy(config),
    ):
        try:
            strategy.on_candle(sample)
            assert False
        except NotImplementedError:
            assert True


def test_sequence_contains_external_and_internal_swings() -> None:
    closes = [
        1.1000,
        1.1010,
        1.1005,
        1.1020,
        1.1015,
        1.1030,
        1.1026,
        1.1040,
        1.1035,
    ]
    engine = SwingEngine(config=SwingConfig(left_bars=1, right_bars=1), event_bus=EventBus())
    engine.run(_series("EURUSD", "M1", closes))
    swings = engine.sequence("EURUSD", "M1")

    assert len(swings) > 0
    assert all(
        swing.classification
        in (
            SwingClassification.SWING_HIGH,
            SwingClassification.SWING_LOW,
            SwingClassification.HIGHER_HIGH,
            SwingClassification.HIGHER_LOW,
            SwingClassification.LOWER_HIGH,
            SwingClassification.LOWER_LOW,
            SwingClassification.EQUAL_HIGH,
            SwingClassification.EQUAL_LOW,
        )
        for swing in swings
    )
