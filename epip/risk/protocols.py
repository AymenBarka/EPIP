"""Risk framework protocols."""

from typing import Protocol

from epip.decision.models import DecisionSnapshot
from epip.risk.models import RiskSnapshot


class RiskEngineProtocol(Protocol):
    def process(self, decision: DecisionSnapshot, **market_data: float) -> RiskSnapshot: ...
