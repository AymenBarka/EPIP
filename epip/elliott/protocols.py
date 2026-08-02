"""EPIP-011 public protocols."""

from typing import Protocol

from epip.context import MarketContextSnapshot
from epip.elliott.models import WaveSnapshot


class ElliottProtocol(Protocol):
    def process(self, context: MarketContextSnapshot) -> WaveSnapshot: ...
