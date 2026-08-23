from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class FibonacciInputValidator:
    def validate(
        self, s: SwingSequence, m: MarketStructureSnapshot, liquidity_snapshot: LiquiditySnapshot
    ) -> bool:
        return (
            len(s.swings) >= 2
            and s.symbol == m.symbol == liquidity_snapshot.symbol
            and s.timeframe == m.timeframe == liquidity_snapshot.timeframe
        )
