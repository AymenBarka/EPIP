from __future__ import annotations

from epip.market_structure.choch_detector import CHOCHDetector
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.models import TrendDirection
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _swing(idx: int, classification: SwingClassification, pivot: PivotType) -> Swing:
    return Swing(
        point=SwingPoint(
            symbol="EURUSD",
            timeframe="M1",
            index=idx,
            timestamp=f"2024-01-01T00:00:{idx:02d}+00:00",
            price=1.1 + idx * 0.001,
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


def test_choch_generated_once_from_uptrend_to_downtrend() -> None:
    detector = CHOCHDetector()
    seq = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing(2, SwingClassification.LOWER_LOW, PivotType.LOW),
        ),
    )

    first = detector.detect(
        seq,
        previous_trend=TrendDirection.UPTREND,
        config=MarketStructureConfig(minimum_swings=2),
    )
    second = detector.detect(
        seq,
        previous_trend=TrendDirection.UPTREND,
        config=MarketStructureConfig(minimum_swings=2),
    )

    assert first is not None
    assert first.new_trend == TrendDirection.DOWNTREND
    assert second is None


def test_no_choch_when_previous_trend_unknown() -> None:
    detector = CHOCHDetector()
    seq = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, SwingClassification.HIGHER_HIGH, PivotType.HIGH),
            _swing(2, SwingClassification.LOWER_LOW, PivotType.LOW),
        ),
    )

    result = detector.detect(
        seq,
        previous_trend=TrendDirection.UNKNOWN,
        config=MarketStructureConfig(minimum_swings=2),
    )
    assert result is None
