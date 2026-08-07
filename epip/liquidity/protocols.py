"""Public liquidity engine protocol."""

from typing import Protocol

from epip.liquidity.history import LiquidityHistory
from epip.liquidity.metrics import LiquidityMetrics
from epip.liquidity.models import LiquiditySnapshot
from epip.market_structure.models import MarketStructureSnapshot
from epip.swing.models import SwingSequence


class LiquidityProtocol(Protocol):
    def process(
        self, structure: MarketStructureSnapshot, sequence: SwingSequence
    ) -> LiquiditySnapshot: ...
    def snapshot(self, symbol: str, timeframe: str) -> LiquiditySnapshot | None: ...
    def history(self, symbol: str, timeframe: str) -> LiquidityHistory: ...
    def metrics(self) -> LiquidityMetrics: ...
