"""Targets derived exclusively from Market Context evidence."""

from epip.context import MarketContextSnapshot
from epip.elliott.models import WaveLabel, WaveTarget


class WaveTargetService:
    def targets(
        self, context: MarketContextSnapshot, label: WaveLabel, probability: float
    ) -> tuple[WaveTarget, ...]:
        fibonacci_levels = context.context.fibonacci_snapshot.extension.levels
        targets = tuple(
            WaveTarget(
                label,
                level.price,
                level.price,
                level.price,
                max(0.0, min(1.0, probability * level.confluence_score)),
            )
            for level in fibonacci_levels[:3]
        )
        if targets:
            return targets
        return tuple(
            WaveTarget(label, pool.price, pool.price, pool.price, probability)
            for pool in context.context.current_liquidity_pools[:3]
        )
