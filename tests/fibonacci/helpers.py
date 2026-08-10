from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import (
    MarketStructure,
    MarketStructureSnapshot,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def inputs(
    symbol: str = "EURUSD", timeframe: str = "M1", trend: TrendDirection = TrendDirection.UPTREND
) -> tuple["SwingSequence", "MarketStructureSnapshot", "LiquiditySnapshot"]:
    swings = SwingSequence(
        symbol,
        timeframe,
        tuple(
            Swing(
                SwingPoint(
                    symbol,
                    timeframe,
                    i,
                    str(i),
                    p,
                    PivotType.LOW if i == 1 else PivotType.HIGH,
                    2,
                    2,
                ),
                SwingClassification.SWING_LOW if i == 1 else SwingClassification.HIGHER_HIGH,
                SwingScope.EXTERNAL,
                2,
                0.1,
                2,
            )
            for i, p in ((1, 1.0), (2, 2.0))
        ),
    )
    t = Trend(trend, 1, "1", "2")
    m = MarketStructureSnapshot(
        "2", MarketStructure(symbol, timeframe, t, StructureState.UPTREND, None, None, None, 2)
    )
    liquidity = LiquiditySnapshot("2", symbol, timeframe, 1)
    return swings, m, liquidity
