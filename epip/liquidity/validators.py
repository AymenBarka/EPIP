"""Liquidity input validation."""

from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class LiquidityInputValidator:
    def validate(self, structure: MarketStructureSnapshot, sequence: SwingSequence) -> bool:
        return bool(
            sequence.swings
            and structure.symbol == sequence.symbol
            and structure.timeframe == sequence.timeframe
        )
