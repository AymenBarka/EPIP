from dataclasses import replace

from epip.context import MarketContextConfig, MarketContextEngine, MarketContextSnapshot
from epip.core.event_bus import EventBus
from epip.elliott import ElliottConfig, ElliottWaveEngine, WaveSnapshot
from epip.market_structure.models import StructureState, TrendDirection
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.types import PivotType, SwingClassification, SwingScope
from tests.context.helpers import official_inputs


def snapshots(
    *,
    symbol: str = "EURUSD",
    timeframe: str = "M15",
    direction: TrendDirection = TrendDirection.UPTREND,
    state: StructureState = StructureState.UPTREND,
    score: float = 0.8,
) -> tuple[MarketContextSnapshot, WaveSnapshot]:
    inputs = official_inputs(symbol, timeframe, direction, state, score)
    context = MarketContextEngine(config=MarketContextConfig(), event_bus=EventBus()).process(
        *inputs
    )
    prices = (1.0, 2.0, 1.5, 3.0, 2.5, 3.5)
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
    context = replace(
        context,
        context=replace(
            context.context,
            swing_snapshot=SwingSequence(symbol, timeframe, swings),
        ),
    )
    elliott = ElliottWaveEngine(config=ElliottConfig(), event_bus=EventBus()).process(context)
    return context, elliott
