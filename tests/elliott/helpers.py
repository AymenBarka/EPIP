from dataclasses import replace

from epip.context import MarketContextConfig, MarketContextEngine, MarketContextSnapshot
from epip.core.event_bus import EventBus
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope
from tests.context.helpers import official_inputs


def market_context(
    prices: tuple[float, ...] = (1.0, 2.0, 1.5, 3.0, 2.5, 3.5),
    *,
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    score: float = 0.8,
) -> MarketContextSnapshot:
    snapshot = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus()).process(
        *official_inputs(symbol, timeframe, score=score)
    )
    swings = tuple(
        Swing(
            SwingPoint(
                symbol,
                timeframe,
                index,
                str(index),
                price,
                PivotType.LOW if index % 2 else PivotType.HIGH,
                2,
                2,
            ),
            SwingClassification.SWING_LOW if index % 2 else SwingClassification.HIGHER_HIGH,
            SwingScope.EXTERNAL,
            1,
            0.5,
            2,
        )
        for index, price in enumerate(prices, 1)
    )
    sequence = SwingSequence(symbol, timeframe, swings)
    return replace(snapshot, context=replace(snapshot.context, swing_snapshot=sequence))
