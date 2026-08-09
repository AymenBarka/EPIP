"""Internal checkpoint transaction for one replay session."""

from __future__ import annotations

from types import TracebackType
from typing import Self

from epip.features.feature_store import FeatureStore, FeatureStoreCheckpoint
from epip.replay.replay_clock import ReplayClockCheckpoint
from epip.replay.replay_scheduler import ReplaySchedulerCheckpoint
from epip.replay.replay_session import ReplaySession, ReplaySessionCheckpoint
from epip.replay.replay_statistics import ReplayStatisticsCheckpoint


class ReplaySessionTransaction:
    """Hold Replay-owned locks and restore checkpoints unless committed."""

    def __init__(self, session: ReplaySession, feature_store: FeatureStore) -> None:
        self._session = session
        self._feature_store = feature_store
        self._committed = False
        self._session_state: ReplaySessionCheckpoint | None = None
        self._clock_state: ReplayClockCheckpoint | None = None
        self._scheduler_state: ReplaySchedulerCheckpoint | None = None
        self._statistics_state: ReplayStatisticsCheckpoint | None = None
        self._feature_state: FeatureStoreCheckpoint | None = None
        self._locks = (
            session._lock,
            session.clock._lock,
            session.scheduler._lock,
            session.statistics._lock,
            feature_store._lock,
        )

    def __enter__(self) -> Self:
        for lock in self._locks:
            lock.acquire()
        try:
            self._session_state = self._session._checkpoint()
            self._clock_state = self._session.clock._checkpoint()
            self._scheduler_state = self._session.scheduler._checkpoint()
            self._statistics_state = self._session.statistics._checkpoint()
            self._feature_state = self._feature_store._checkpoint()
        except BaseException:
            for lock in reversed(self._locks):
                lock.release()
            raise
        return self

    def commit(self) -> None:
        self._committed = True

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_value: BaseException | None,
        traceback: TracebackType | None,
    ) -> None:
        try:
            if not self._committed or exc_type is not None:
                assert self._session_state is not None
                assert self._clock_state is not None
                assert self._scheduler_state is not None
                assert self._statistics_state is not None
                assert self._feature_state is not None
                self._session._restore(self._session_state)
                self._session.clock._restore(self._clock_state)
                self._session.scheduler._restore(self._scheduler_state)
                self._session.statistics._restore(self._statistics_state)
                self._feature_store._restore(self._feature_state)
        finally:
            for lock in reversed(self._locks):
                lock.release()
