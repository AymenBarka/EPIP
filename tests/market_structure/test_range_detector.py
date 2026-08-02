from __future__ import annotations

from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.range_detector import RangeDetector
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _swing(idx: int, price: float, classification: SwingClassification, pivot: PivotType) -> Swing:
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
        classification=classification,
        scope=SwingScope.INTERNAL,
        distance_from_previous=1,
        price_move_from_previous=0.0001,
        detection_latency_bars=2,
    )


def test_range_detected_with_repeated_touches() -> None:
    detector = RangeDetector()
    seq = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, 1.2000, SwingClassification.SWING_HIGH, PivotType.HIGH),
            _swing(2, 1.1000, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing(3, 1.1998, SwingClassification.EQUAL_HIGH, PivotType.HIGH),
            _swing(4, 1.1002, SwingClassification.EQUAL_LOW, PivotType.LOW),
            _swing(5, 1.1999, SwingClassification.EQUAL_HIGH, PivotType.HIGH),
        ),
    )
    cfg = MarketStructureConfig(minimum_swings=2, equal_threshold=0.00001, range_touch_count=2)

    range_regime = detector.detect(seq, cfg)

    assert range_regime is not None
    assert range_regime.touches_high >= 2
    assert range_regime.touches_low >= 2


def test_range_not_detected_on_false_breakout() -> None:
    detector = RangeDetector()
    seq = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, 1.2000, SwingClassification.SWING_HIGH, PivotType.HIGH),
            _swing(2, 1.1000, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing(3, 1.2500, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing(4, 1.0500, SwingClassification.LOWER_LOW, PivotType.LOW),
            _swing(5, 1.2600, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
        ),
    )

    range_regime = detector.detect(
        seq, MarketStructureConfig(minimum_swings=2, range_touch_count=2)
    )
    assert range_regime is None
