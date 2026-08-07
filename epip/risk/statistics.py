"""Thread-safe risk statistics."""

from threading import RLock

from epip.risk.models import PositionPlan, RiskMetrics


class RiskStatistics:
    def __init__(self) -> None:
        self._plans = self._accepted = self._rejected = 0
        self._risk = self._latency = 0.0
        self._lock = RLock()

    def record(self, plan: PositionPlan, latency: float) -> None:
        with self._lock:
            self._plans += 1
            self._accepted += int(plan.accepted)
            self._rejected += int(not plan.accepted)
            self._risk += plan.position_size.risk_amount
            self._latency += latency

    def snapshot(self) -> RiskMetrics:
        with self._lock:
            count = self._plans or 1
            return RiskMetrics(
                self._plans,
                self._accepted,
                self._rejected,
                self._risk / count,
                self._latency / count,
            )
