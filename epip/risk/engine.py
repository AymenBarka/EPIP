"""Thread-safe official EPIP position planning engine."""

import logging
from threading import RLock
from time import perf_counter
from typing import Any

from epip.core.event_bus import EventBus
from epip.decision.models import DecisionSnapshot
from epip.risk.analyzer import RiskAnalyzer
from epip.risk.config import RiskConfig
from epip.risk.events import (
    DrawdownExceeded,
    ExposureExceeded,
    PositionPlanned,
    RiskAccepted,
    RiskRejected,
)
from epip.risk.graph import RiskGraph
from epip.risk.history import RiskHistory
from epip.risk.models import RiskMetrics, RiskSnapshot
from epip.risk.statistics import RiskStatistics
from epip.risk.validators import validate_config, validate_decision


class RiskEngine:
    def __init__(
        self, *, config: RiskConfig, event_bus: EventBus, logger: logging.Logger | None = None
    ) -> None:
        validate_config(config)
        self._config = config
        self._bus = event_bus
        self._logger = logger or logging.getLogger("epip.risk")
        self._analyzer = RiskAnalyzer(config)
        self._statistics = RiskStatistics()
        self._snapshots: dict[tuple[str, str], RiskSnapshot] = {}
        self._histories: dict[tuple[str, str], RiskHistory] = {}
        self._graphs: dict[tuple[str, str], RiskGraph] = {}
        self._lock = RLock()

    def process(self, decision: DecisionSnapshot, **market_data: Any) -> RiskSnapshot:
        validate_decision(decision)
        key = (decision.symbol, decision.timeframe)
        with self._lock:
            started = perf_counter()
            previous = self._snapshots.get(key)
            plan = self._analyzer.analyze(decision, **market_data)
            snapshot = RiskSnapshot(
                decision.timestamp,
                decision.symbol,
                decision.timeframe,
                previous.version + 1 if previous else 1,
                decision.version,
                plan,
                self._config.engine_version,
            )
            self._snapshots[key] = snapshot
            self._histories[key] = self._histories.get(key, RiskHistory()).append(snapshot)
            self._graphs[key] = self._graphs.get(key, RiskGraph()).append(snapshot)
            self._statistics.record(plan, perf_counter() - started)
            self._publish(snapshot)
            self._logger.debug("risk plan v%d created for %s", snapshot.version, key)
            return snapshot

    def snapshot(self, symbol: str, timeframe: str) -> RiskSnapshot | None:
        with self._lock:
            return self._snapshots.get((symbol, timeframe))

    def history(self, symbol: str, timeframe: str) -> RiskHistory:
        with self._lock:
            return self._histories.get((symbol, timeframe), RiskHistory())

    def graph(self, symbol: str, timeframe: str) -> RiskGraph:
        with self._lock:
            return self._graphs.get((symbol, timeframe), RiskGraph())

    def metrics(self) -> RiskMetrics:
        return self._statistics.snapshot()

    def _publish(self, snapshot: RiskSnapshot) -> None:
        plan = snapshot.plan
        event_id = f"risk-{snapshot.symbol}-{snapshot.version}"
        self._bus.publish(
            PositionPlanned(
                id=event_id,
                timestamp=snapshot.timestamp,
                symbol=snapshot.symbol,
                decision_id=plan.decision_id,
                plan_id=plan.plan_id,
                accepted=plan.accepted,
            )
        )
        if plan.accepted:
            self._bus.publish(
                RiskAccepted(
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    decision_id=plan.decision_id,
                    plan_id=plan.plan_id,
                )
            )
        else:
            failed = ",".join(reason.code for reason in plan.reasons if not reason.accepted)
            self._bus.publish(
                RiskRejected(
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    decision_id=plan.decision_id,
                    plan_id=plan.plan_id,
                    reason=failed,
                )
            )
        if any(not reason.accepted and "EXPOSURE" in reason.code for reason in plan.reasons):
            self._bus.publish(
                ExposureExceeded(
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    decision_id=plan.decision_id,
                    plan_id=plan.plan_id,
                    exposure=plan.exposure.total_exposure,
                )
            )
        if any(not reason.accepted and reason.code == "DRAWDOWN" for reason in plan.reasons):
            self._bus.publish(
                DrawdownExceeded(
                    id=event_id,
                    timestamp=snapshot.timestamp,
                    symbol=snapshot.symbol,
                    decision_id=plan.decision_id,
                    plan_id=plan.plan_id,
                    drawdown=1.0,
                )
            )
