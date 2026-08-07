"""Portfolio protocols."""

from typing import Protocol

from epip.execution.models import ExecutionSnapshot
from epip.portfolio.models import PortfolioSnapshot


class PortfolioEngineProtocol(Protocol):
    def process(self, execution: ExecutionSnapshot) -> PortfolioSnapshot: ...
