from __future__ import annotations

from epip.core.event_bus import EventBus
from epip.market_structure.config import MarketStructureConfig
from epip.market_structure.engine import MarketStructureEngine
from epip.market_structure.models import StructureQuality
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def _swing(idx: int, classification: SwingClassification, pivot: PivotType, price: float) -> Swing:
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
        distance_from_previous=3,
        price_move_from_previous=0.001,
        detection_latency_bars=2,
    )


def test_structure_confidence_and_quality_are_deterministic() -> None:
    sequence = SwingSequence(
        symbol="EURUSD",
        timeframe="M1",
        swings=(
            _swing(1, SwingClassification.SWING_LOW, PivotType.LOW, 1.1),
            _swing(2, SwingClassification.HIGHER_HIGH, PivotType.HIGH, 1.2),
            _swing(3, SwingClassification.HIGHER_LOW, PivotType.LOW, 1.15),
            _swing(4, SwingClassification.HIGHER_HIGH, PivotType.HIGH, 1.25),
            _swing(5, SwingClassification.HIGHER_LOW, PivotType.LOW, 1.2),
        ),
    )

    engine = MarketStructureEngine(
        config=MarketStructureConfig(minimum_swings=4), event_bus=EventBus()
    )

    first = engine.process_sequence(sequence)
    second = engine.process_sequence(sequence)

    assert first.confidence == second.confidence
    assert first.quality == second.quality
    assert 0.0 <= first.confidence <= 1.0
    assert first.quality in (
        StructureQuality.LOW,
        StructureQuality.MEDIUM,
        StructureQuality.HIGH,
        StructureQuality.VERY_HIGH,
    )
