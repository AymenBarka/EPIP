"""Protocols for the core domain contracts."""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from epip.core.context import MarketContext
from epip.core.decision import Decision
from epip.core.evidence import Evidence
from epip.core.scenario import Scenario


@runtime_checkable
class EvidenceProducer(Protocol):
    """Protocol for components that produce evidence."""

    def produce(self, context: MarketContext) -> Evidence:
        """Produce a single evidence item from a market context."""


@runtime_checkable
class ScenarioBuilder(Protocol):
    """Protocol for components that build scenarios."""

    def build(self, context: MarketContext, evidence: tuple[Evidence, ...]) -> Scenario:
        """Build a scenario from a market context and evidence."""


@runtime_checkable
class DecisionConsumer(Protocol):
    """Protocol for components that consume decisions."""

    def consume(self, decision: Decision) -> None:
        """Handle a final decision."""
