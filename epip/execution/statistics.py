"""Thread-safe execution statistics collector."""

from threading import RLock

from epip.execution.models import ExecutionReport, ExecutionStatistics


class StatisticsCollector:
    def __init__(self) -> None:
        self._orders = self._filled = self._rejected = self._retries = 0
        self._latency = self._slippage = self._commission = 0.0
        self._lock = RLock()

    def record(self, report: ExecutionReport, latency: float, retries: int) -> None:
        with self._lock:
            self._orders += 1
            self._filled += int(report.completed)
            self._rejected += int(not report.completed)
            self._retries += retries
            self._latency += latency
            self._slippage += report.slippage
            self._commission += report.commission

    def snapshot(self) -> ExecutionStatistics:
        with self._lock:
            count = self._orders or 1
            return ExecutionStatistics(
                self._orders,
                self._filled,
                self._rejected,
                self._retries,
                self._latency / count,
                self._slippage / count,
                self._commission,
            )
