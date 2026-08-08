"""Kernel orchestrating the EPIP execution pipeline."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from time import perf_counter
from typing import Any

from epip.core.context import MarketContext
from epip.core.decision import Decision
from epip.core.event_bus import EventBus
from epip.core.events import BaseEvent, DecisionCreated, EvidenceCreated, ScenarioCreated
from epip.core.evidence import Evidence
from epip.core.hypothesis import Hypothesis
from epip.core.identity import (
    ClockProtocol,
    DeterministicClock,
    DeterministicIdGenerator,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import integrity_boundary
from epip.core.plugin_context import PluginContext
from epip.core.plugin_protocol import PluginProtocol
from epip.core.plugin_result import PluginResult
from epip.core.registry import Registry
from epip.core.scenario import Scenario
from epip.core.types import DecisionType, Direction, ScenarioType
from epip.core.value_objects import Probability, RiskScore


@dataclass(frozen=True, slots=True)
class KernelResult:
    """Outcome returned by the kernel after a run."""

    plugin_results: tuple[PluginResult, ...]
    evidence: tuple[Evidence, ...]
    scenario: Scenario | None
    hypothesis: Hypothesis | None
    decision: Decision | None


class Kernel:
    """Core orchestration layer that runs plugins via the registry and event bus."""

    def __init__(
        self,
        registry: Registry | None = None,
        event_bus: EventBus | None = None,
        logger: logging.Logger | None = None,
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        self.registry = registry or Registry()
        self.event_bus = event_bus or EventBus()
        self.logger = logger or logging.getLogger("epip.kernel")
        self._deterministic = isinstance(clock, DeterministicClock) and isinstance(
            id_generator, DeterministicIdGenerator
        )
        self._clock = resolve_clock(clock)
        self._id_generator = resolve_id_generator(id_generator)

    @integrity_boundary
    def run(self, market_context: MarketContext) -> KernelResult:
        """Execute the active plugins against a market context."""
        plugin_context = PluginContext(
            market_context=market_context,
            event_bus=self.event_bus,
            registry=self.registry,
            clock=self._clock,
            id_generator=self._id_generator,
        )
        plugin_results: list[PluginResult] = []
        evidence: list[Evidence] = []

        for plugin in self.registry.ordered_plugins():
            plugin_name = self._resolve_name(plugin)
            self.logger.info("plugin start: %s", plugin_name)
            started = perf_counter()
            try:
                raw_result = plugin.execute(plugin_context)
                execution_time = perf_counter() - started
                normalized = self._normalize_result(plugin, raw_result, execution_time)
                if not normalized.success:
                    self.logger.warning("plugin failed: %s", plugin_name)
                self.logger.info("plugin end: %s (%s s)", plugin_name, execution_time)
            except Exception as exc:  # pragma: no cover - exercised by tests
                execution_time = perf_counter() - started
                normalized = PluginResult(
                    plugin=plugin_name,
                    execution_time=self._runtime(execution_time),
                    success=False,
                    errors=(str(exc),),
                    warnings=(),
                    generated_evidence=(),
                    metadata={},
                )
                self.logger.exception("plugin exception: %s", plugin_name)
            plugin_results.append(normalized)
            evidence.extend(normalized.generated_evidence)

        scenario: Scenario | None = None
        hypothesis: Hypothesis | None = None
        decision: Decision | None = None
        if evidence:
            direction = self._derive_direction(evidence)
            probability = Probability(
                sum(float(item.confidence) for item in evidence) / len(evidence),
                clock=self._clock,
                id_generator=self._id_generator,
            )
            scenario = Scenario(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"scenario-{market_context.timestamp}",
                direction=direction,
                scenario_type=ScenarioType.CONTINUATION,
                evidence=tuple(evidence),
                probability=probability,
                timestamp=market_context.timestamp,
            )
            hypothesis = Hypothesis(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"hypothesis-{market_context.timestamp}",
                scenario=scenario,
                timestamp=market_context.timestamp,
            )
            decision = Decision(
                clock=self._clock,
                id_generator=self._id_generator,
                id=f"decision-{market_context.timestamp}",
                decision_type=self._derive_decision_type(direction),
                reason="aggregated from plugins",
                probability=probability,
                risk_score=RiskScore(0.0, clock=self._clock, id_generator=self._id_generator),
                timestamp=market_context.timestamp,
            )

            self.event_bus.publish(
                ScenarioCreated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id="scenario-created",
                    timestamp=market_context.timestamp,
                    scenario_id=scenario.id,
                )
            )
            self.event_bus.publish(
                DecisionCreated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id="decision-created",
                    timestamp=market_context.timestamp,
                    decision_id=decision.id,
                )
            )

        for item in evidence:
            self.event_bus.publish(
                EvidenceCreated(
                    clock=self._clock,
                    id_generator=self._id_generator,
                    id=f"evidence-{item.id}",
                    timestamp=market_context.timestamp,
                    evidence_id=item.id,
                )
            )

        if hypothesis is not None:
            self.event_bus.publish(
                BaseEvent(
                    id="hypothesis-created",
                    timestamp=market_context.timestamp,
                    clock=self._clock,
                    id_generator=self._id_generator,
                )
            )

        return KernelResult(
            plugin_results=tuple(plugin_results),
            evidence=tuple(evidence),
            scenario=scenario,
            hypothesis=hypothesis,
            decision=decision,
        )

    def _normalize_result(
        self, plugin: PluginProtocol, raw_result: Any, execution_time: float
    ) -> PluginResult:
        if isinstance(raw_result, PluginResult):
            return PluginResult(
                plugin=self._resolve_name(plugin),
                execution_time=self._runtime(execution_time),
                success=raw_result.success,
                errors=raw_result.errors,
                warnings=raw_result.warnings,
                generated_evidence=raw_result.generated_evidence,
                metadata=raw_result.metadata,
            )
        if isinstance(raw_result, Evidence):
            return PluginResult(
                plugin=self._resolve_name(plugin),
                execution_time=self._runtime(execution_time),
                success=True,
                generated_evidence=(raw_result,),
                metadata={},
            )
        if isinstance(raw_result, tuple) and all(isinstance(item, Evidence) for item in raw_result):
            return PluginResult(
                plugin=self._resolve_name(plugin),
                execution_time=self._runtime(execution_time),
                success=True,
                generated_evidence=raw_result,
                metadata={},
            )
        return PluginResult(
            plugin=self._resolve_name(plugin),
            execution_time=self._runtime(execution_time),
            success=False,
            errors=("unsupported result payload",),
            warnings=(),
            generated_evidence=(),
            metadata={},
        )

    def _resolve_name(self, plugin: PluginProtocol) -> str:
        return getattr(plugin, "name", plugin.__class__.__name__)

    def _runtime(self, value: float) -> float:
        """Exclude wall-clock measurements from deterministic results."""
        return 0.0 if self._deterministic else value

    def _derive_direction(self, evidence_items: list[Evidence]) -> Direction:
        if not evidence_items:
            return Direction.NEUTRAL
        if any(item.direction == Direction.SELL for item in evidence_items):
            return Direction.SELL
        if any(item.direction == Direction.BUY for item in evidence_items):
            return Direction.BUY
        return Direction.NEUTRAL

    def _derive_decision_type(self, direction: Direction) -> DecisionType:
        if direction == Direction.SELL:
            return DecisionType.SELL
        if direction == Direction.BUY:
            return DecisionType.BUY
        return DecisionType.WAIT
