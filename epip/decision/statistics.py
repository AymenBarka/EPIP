"""Thread-safe Decision Engine statistics."""

from threading import RLock

from epip.decision.metrics import DecisionMetrics
from epip.decision.models import DecisionAction, DecisionSnapshot


class DecisionStatistics:
    def __init__(self) -> None:
        self._decisions = 0
        self._long = 0
        self._short = 0
        self._wait = 0
        self._invalid = 0
        self._score = 0.0
        self._elapsed = 0.0
        self._maximum = 0.0
        self._lock = RLock()

    def record(self, snapshot: DecisionSnapshot, elapsed: float) -> None:
        with self._lock:
            action = snapshot.decision.action
            self._decisions += 1
            self._long += int(action in (DecisionAction.LONG, DecisionAction.ADD))
            self._short += int(action == DecisionAction.SHORT)
            self._wait += int(action in (DecisionAction.WAIT, DecisionAction.REDUCE))
            self._invalid += int(action == DecisionAction.INVALID)
            self._score += snapshot.decision.score.total
            self._elapsed += elapsed
            self._maximum = max(self._maximum, elapsed)

    def snapshot(self) -> DecisionMetrics:
        with self._lock:
            return DecisionMetrics(
                self._decisions,
                self._long,
                self._short,
                self._wait,
                self._invalid,
                self._score / self._decisions if self._decisions else 0.0,
                self._elapsed,
                self._maximum,
            )
