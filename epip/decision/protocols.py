"""EPIP-012 public protocols."""

from typing import Protocol

from epip.context import MarketContextSnapshot
from epip.decision.models import DecisionSnapshot
from epip.elliott import WaveSnapshot


class DecisionProtocol(Protocol):
    def process(
        self, context: MarketContextSnapshot, elliott: WaveSnapshot
    ) -> DecisionSnapshot: ...
