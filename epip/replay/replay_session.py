"""Replay session aggregate holding all replay runtime components."""

from __future__ import annotations

from collections import deque
from collections.abc import Mapping
from threading import RLock

from epip.core.candle import Candle
from epip.core.context import MarketContext
from epip.replay.replay_clock import ReplayClock
from epip.replay.replay_config import ReplayConfig
from epip.replay.replay_scheduler import ReplayScheduler
from epip.replay.replay_state import ReplayState
from epip.replay.replay_statistics import ReplayStatistics


class ReplaySession:
    """Mutable runtime session encapsulating replay state and caches."""

    def __init__(
        self,
        *,
        config: ReplayConfig,
        clock: ReplayClock,
        statistics: ReplayStatistics,
        scheduler: ReplayScheduler,
    ) -> None:
        self.config = config
        self.clock = clock
        self.statistics = statistics
        self.scheduler = scheduler
        self._lock = RLock()
        self._state = ReplayState.CREATED
        self._contexts: dict[tuple[str, str], MarketContext] = {}
        self._candle_windows: dict[tuple[str, str], deque[Candle]] = {}
        self._session_id = f"replay-{id(self)}"

    @property
    def session_id(self) -> str:
        return self._session_id

    def state(self) -> ReplayState:
        with self._lock:
            return self._state

    def set_state(self, state: ReplayState) -> None:
        with self._lock:
            self._state = state

    def current_context(self, symbol: str, timeframe: str) -> MarketContext | None:
        with self._lock:
            return self._contexts.get((symbol, timeframe))

    def set_context(self, context: MarketContext) -> None:
        with self._lock:
            self._contexts[(context.symbol, context.timeframe)] = context

    def window_for(self, symbol: str, timeframe: str) -> deque[Candle]:
        with self._lock:
            key = (symbol, timeframe)
            if key not in self._candle_windows:
                maxlen = max(1, self.config.warmup_bars + 1)
                self._candle_windows[key] = deque(maxlen=maxlen)
            return self._candle_windows[key]

    def contexts(self) -> Mapping[tuple[str, str], MarketContext]:
        with self._lock:
            return dict(self._contexts)
