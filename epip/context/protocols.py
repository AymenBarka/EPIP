"""Public Market Context engine protocol."""

from typing import Protocol

from epip.context.snapshot import MarketContextSnapshot
from epip.fibonacci.models import FibonacciSnapshot
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class MarketContextProtocol(Protocol):
    def process(
        self,
        swings: SwingSequence,
        structure: MarketStructureSnapshot,
        liquidity: LiquiditySnapshot,
        fibonacci: FibonacciSnapshot,
    ) -> MarketContextSnapshot: ...
