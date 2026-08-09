"""Streaming swing detector orchestrating strategy, validation, and filtering."""

from __future__ import annotations

import logging
from copy import deepcopy
from threading import RLock

from epip.core.candle import Candle
from epip.swing.config import SwingConfig
from epip.swing.filters import CompositeSwingFilter, build_default_filters
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.pivot_detector import create_default_strategy
from epip.swing.protocols import PivotStrategyProtocol
from epip.swing.types import PivotType, SwingClassification, SwingKey, SwingScope
from epip.swing.validators import PivotValidator, PriceValidator, SequenceValidator


class SwingDetector:
    """Official EPIP-006 source of swing points and classifications."""

    def __init__(
        self,
        *,
        config: SwingConfig,
        swing_filter: CompositeSwingFilter | None = None,
        logger: logging.Logger | None = None,
    ) -> None:
        self._config = config
        self._logger = logger or logging.getLogger("epip.swing.detector")
        self._filters = swing_filter or build_default_filters()
        self._price_validator = PriceValidator()
        self._pivot_validator = PivotValidator()
        self._sequence_validator = SequenceValidator()
        self._strategies: dict[SwingKey, PivotStrategyProtocol] = {}
        self._sequences: dict[SwingKey, list[Swing]] = {}
        self._lock = RLock()

    def process(self, candle: Candle) -> tuple[Swing, ...]:
        """Push one candle and return accepted swings for its stream."""
        if not self._price_validator.validate(candle):
            self._logger.debug("price validation rejected candle %s", candle.timestamp)
            return ()

        key: SwingKey = (candle.symbol, candle.timeframe)
        with self._lock:
            strategy = self._strategies.setdefault(key, create_default_strategy(self._config))
            sequence_list = self._sequences.setdefault(key, [])

        accepted: list[Swing] = []
        for point in strategy.on_candle(candle):
            if not self._pivot_validator.validate(point):
                self._logger.debug("pivot validation rejected point %s", point.timestamp)
                continue

            with self._lock:
                sequence = SwingSequence(
                    symbol=key[0], timeframe=key[1], swings=tuple(sequence_list)
                )
                candidate = self._build_swing(point, sequence)
                if not self._sequence_validator.validate(sequence, candidate):
                    continue
                if not self._filters.allow(candidate, sequence, self._config):
                    continue
                sequence_list.append(candidate)
                accepted.append(candidate)

        return tuple(accepted)

    def sequence(self, symbol: str, timeframe: str) -> SwingSequence:
        """Return immutable sequence snapshot for one stream."""
        key: SwingKey = (symbol, timeframe)
        with self._lock:
            swings = tuple(self._sequences.get(key, ()))
        return SwingSequence(symbol=symbol, timeframe=timeframe, swings=swings)

    def _checkpoint(
        self,
    ) -> tuple[
        dict[SwingKey, PivotStrategyProtocol],
        dict[SwingKey, list[Swing]],
    ]:
        """Capture private mutable detector state for an engine transaction."""
        with self._lock:
            return deepcopy(self._strategies), deepcopy(self._sequences)

    def _restore(
        self,
        checkpoint: tuple[
            dict[SwingKey, PivotStrategyProtocol],
            dict[SwingKey, list[Swing]],
        ],
    ) -> None:
        """Restore a checkpoint after a failed pre-commit operation."""
        with self._lock:
            self._strategies, self._sequences = checkpoint

    def _build_swing(self, point: SwingPoint, sequence: SwingSequence) -> Swing:
        last = sequence.last()
        distance = point.index - last.point.index if last is not None else 0
        move = point.price - last.point.price if last is not None else 0.0
        classification = self._classify(point, sequence)
        scope = self._scope(distance)
        return Swing(
            point=point,
            classification=classification,
            scope=scope,
            distance_from_previous=max(0, distance),
            price_move_from_previous=move,
            detection_latency_bars=point.right_bars,
        )

    def _classify(self, point: SwingPoint, sequence: SwingSequence) -> SwingClassification:
        if point.pivot_type == PivotType.HIGH:
            previous = sequence.last_by_pivot_type(PivotType.HIGH)
            if previous is None:
                return SwingClassification.SWING_HIGH
            delta = point.price - previous.point.price
            if abs(delta) <= self._config.equal_high_threshold:
                return SwingClassification.EQUAL_HIGH
            return (
                SwingClassification.HIGHER_HIGH if delta > 0.0 else SwingClassification.LOWER_HIGH
            )

        previous = sequence.last_by_pivot_type(PivotType.LOW)
        if previous is None:
            return SwingClassification.SWING_LOW
        delta = point.price - previous.point.price
        if abs(delta) <= self._config.equal_low_threshold:
            return SwingClassification.EQUAL_LOW
        return SwingClassification.HIGHER_LOW if delta > 0.0 else SwingClassification.LOWER_LOW

    def _scope(self, distance_from_previous: int) -> SwingScope:
        if distance_from_previous <= max(2, self._config.minimum_distance * 2):
            return SwingScope.INTERNAL
        return SwingScope.EXTERNAL
