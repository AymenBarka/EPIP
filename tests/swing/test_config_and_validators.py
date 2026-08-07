from __future__ import annotations

from epip.core.candle import Candle
from epip.swing.config import SwingConfig
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope
from epip.swing.validators import PivotValidator, PriceValidator, SequenceValidator


def _point(idx: int, pivot: PivotType, price: float) -> SwingPoint:
    return SwingPoint(
        symbol="EURUSD",
        timeframe="M1",
        index=idx,
        timestamp=f"2024-01-01T00:00:{idx:02d}+00:00",
        price=price,
        pivot_type=pivot,
        left_bars=2,
        right_bars=2,
    )


def _swing(point: SwingPoint, classification: SwingClassification) -> Swing:
    return Swing(
        point=point,
        classification=classification,
        scope=SwingScope.EXTERNAL,
        distance_from_previous=3,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def test_config_validation() -> None:
    try:
        SwingConfig(left_bars=0)
        assert False
    except ValueError:
        assert True

    try:
        SwingConfig(right_bars=0)
        assert False
    except ValueError:
        assert True

    cfg = SwingConfig(left_bars=2, right_bars=2, minimum_distance=1)
    assert cfg.left_bars == 2


def test_price_validator_accepts_valid_candle() -> None:
    validator = PriceValidator()
    candle = Candle(
        timestamp="2024-01-01T00:00:00+00:00",
        symbol="EURUSD",
        timeframe="M1",
        open=1.1,
        high=1.2,
        low=1.0,
        close=1.15,
        volume=1000.0,
    )
    assert validator.validate(candle)


def test_pivot_validator_and_sequence_validator() -> None:
    pivot_validator = PivotValidator()
    sequence_validator = SequenceValidator()

    first = _swing(_point(10, PivotType.HIGH, 1.2), SwingClassification.SWING_HIGH)
    second_ok = _swing(_point(15, PivotType.LOW, 1.1), SwingClassification.SWING_LOW)
    second_bad = _swing(_point(12, PivotType.HIGH, 1.25), SwingClassification.HIGHER_HIGH)

    sequence = SwingSequence(symbol="EURUSD", timeframe="M1", swings=(first,))

    assert pivot_validator.validate(first.point)
    assert sequence_validator.validate(sequence, second_ok)
    assert not sequence_validator.validate(sequence, second_bad)
