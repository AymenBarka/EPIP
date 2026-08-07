"""Thread-safe portfolio statistics."""

from threading import RLock

from epip.portfolio.models import PortfolioMetrics, PortfolioSnapshot


class PortfolioStatistics:
    def __init__(self) -> None:
        self._count = self._breaches = 0
        self._latency = 0.0
        self._latest: PortfolioSnapshot | None = None
        self._lock = RLock()

    def record(self, snapshot: PortfolioSnapshot, latency: float) -> None:
        with self._lock:
            self._count += 1
            self._latency += latency
            self._breaches += int(bool(snapshot.state.limit_reasons))
            self._latest = snapshot

    def snapshot(self) -> PortfolioMetrics:
        with self._lock:
            if self._latest is None:
                return PortfolioMetrics()
            state = self._latest.state
            return PortfolioMetrics(
                self._count,
                len(state.positions),
                state.pnl.realized,
                state.exposure.gross_exposure,
                self._latency / self._count,
                self._breaches,
            )
