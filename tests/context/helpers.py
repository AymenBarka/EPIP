from dataclasses import replace

from epip.core.event_bus import EventBus
from epip.fibonacci import FibonacciConfig, FibonacciEngine
from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import (
    LiquidityPool,
    LiquidityScope,
    LiquiditySide,
    LiquiditySnapshot,
)
from epip.market_structure.models import (
    MarketStructure,
    MarketStructureSnapshot,
    StructureState,
    Trend,
    TrendDirection,
)
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope


def official_inputs(
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    direction: TrendDirection = TrendDirection.UPTREND,
    state: StructureState = StructureState.UPTREND,
    score: float = 0.6,
) -> tuple[SwingSequence, MarketStructureSnapshot, LiquiditySnapshot, FibonacciSnapshot]:
    swings = SwingSequence(
        symbol,
        timeframe,
        (
            Swing(
                SwingPoint(symbol, timeframe, 1, "1", 1.0, PivotType.LOW, 2, 2),
                SwingClassification.SWING_LOW,
                SwingScope.EXTERNAL,
                2,
                0.1,
                2,
            ),
            Swing(
                SwingPoint(symbol, timeframe, 2, "2", 2.0, PivotType.HIGH, 2, 2),
                SwingClassification.HIGHER_HIGH,
                SwingScope.EXTERNAL,
                2,
                1.0,
                2,
            ),
        ),
    )
    trend = Trend(direction, 1, "1", "2")
    structure = MarketStructureSnapshot(
        "2",
        MarketStructure(
            symbol,
            timeframe,
            trend,
            state,
            None,
            None,
            None,
            2,
            confidence=score,
        ),
    )
    pool = LiquidityPool(
        "pool-1",
        symbol,
        timeframe,
        1.5,
        LiquiditySide.BUY_SIDE,
        LiquidityScope.EXTERNAL,
        2,
        (1, 2),
        confluence_score=score,
    )
    liquidity = LiquiditySnapshot("2", symbol, timeframe, 1, pools=(pool,))
    fibonacci = FibonacciEngine(config=FibonacciConfig(), event_bus=EventBus()).process(
        swings, structure, liquidity
    )
    return (
        swings,
        structure,
        liquidity,
        replace(fibonacci, confluence_score=score, probability=score),
    )
