from epip.market_structure.models import (
    MarketStructure,
    MarketStructureSnapshot,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def swing(
    index: int,
    price: float,
    pivot: PivotType,
    classification: SwingClassification,
    scope: SwingScope = SwingScope.EXTERNAL,
) -> Swing:
    return Swing(
        SwingPoint(
            "EURUSD", "M1", index, f"2024-01-01T00:00:{index:02d}+00:00", price, pivot, 2, 2
        ),
        classification,
        scope,
        2,
        0.01,
        2,
    )


def sequence(
    last_price: float = 1.21, symbol: str = "EURUSD", timeframe: str = "M1"
) -> SwingSequence:
    values = (
        swing(1, 1.20, PivotType.HIGH, SwingClassification.SWING_HIGH),
        swing(2, 1.10, PivotType.LOW, SwingClassification.SWING_LOW, SwingScope.INTERNAL),
        swing(3, 1.20005, PivotType.HIGH, SwingClassification.EQUAL_HIGH),
        swing(4, 1.10004, PivotType.LOW, SwingClassification.EQUAL_LOW),
        swing(5, last_price, PivotType.HIGH, SwingClassification.HIGHER_HIGH),
    )
    return SwingSequence(
        symbol,
        timeframe,
        tuple(
            Swing(
                SwingPoint(
                    symbol,
                    timeframe,
                    x.point.index,
                    x.point.timestamp,
                    x.point.price,
                    x.point.pivot_type,
                    2,
                    2,
                ),
                x.classification,
                x.scope,
                2,
                0.01,
                2,
            )
            for x in values
        ),
    )


def structure(symbol: str = "EURUSD", timeframe: str = "M1") -> MarketStructureSnapshot:
    trend = Trend(
        TrendDirection.UPTREND, 1, "2024-01-01T00:00:01+00:00", "2024-01-01T00:00:05+00:00"
    )
    value = MarketStructure(symbol, timeframe, trend, StructureState.UPTREND, None, None, None, 5)
    return MarketStructureSnapshot("2024-01-01T00:00:05+00:00", value)
