"""Validation of official upstream Market Context inputs."""

from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class MarketContextValidator:
    def validate(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        fibonacci: FibonacciSnapshot,
    ) -> bool:
        streams = {
            (swings.symbol, swings.timeframe),
            (structure.symbol, structure.timeframe),
            (liquidity.symbol, liquidity.timeframe),
            (fibonacci.symbol, fibonacci.timeframe),
        }
        return (
            len(streams) == 1
            and fibonacci.structure_version == structure.version
            and fibonacci.liquidity_version == liquidity.version
            and liquidity.structure_version == structure.version
        )
