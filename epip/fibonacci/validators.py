from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class FibonacciInputValidator:
    def validate(self, s: SwingSequence, m: MarketStructureSnapshot, l: LiquiditySnapshot) -> bool:
        return (
            len(s.swings) >= 2
            and s.symbol == m.symbol == l.symbol
            and s.timeframe == m.timeframe == l.timeframe
        )
