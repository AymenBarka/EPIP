from __future__ import annotations

from epip.market_structure.bos_detector import BOSDetector
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.models import TrendDirection
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
        scope=SwingScope.EXTERNAL,
        distance_from_previous=2,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def test_bullish_and_duplicate_bos_detection() -> None:
    detector = BOSDetector()
    sequence = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, 1.10, SwingClassification.SWING_LOW, PivotType.LOW),
            _swing(2, 1.20, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
        ),
    )
    cfg = MarketStructureConfig(minimum_swings=2)

    first = detector.detect(sequence, trend=TrendDirection.UPTREND, config=cfg)
    second = detector.detect(sequence, trend=TrendDirection.UPTREND, config=cfg)

    assert first is not None
    assert first.direction == TrendDirection.UPTREND
    assert second is None


def test_bearish_bos_detection() -> None:
    detector = BOSDetector()
    sequence = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, 1.20, SwingClassification.SWING_HIGH, PivotType.HIGH),
            _swing(2, 1.10, SwingClassification.LOWER_LOW, PivotType.LOW),
        ),
    )

    bos = detector.detect(
        sequence,
        trend=TrendDirection.DOWNTREND,
        config=MarketStructureConfig(minimum_swings=2),
    )

    assert bos is not None
    assert bos.direction == TrendDirection.DOWNTREND
