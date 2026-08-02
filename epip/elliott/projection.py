"""Next-wave projection using official Market Context levels."""

from epip.context import MarketContextSnapshot
from epip.elliott.models import WaveCount, WaveLabel, WaveProjection
from epip.elliott.targets import WaveTargetService


class WaveProjectionService:
    _ORDER = (
        WaveLabel.WAVE_1,
        WaveLabel.WAVE_2,
        WaveLabel.WAVE_3,
        WaveLabel.WAVE_4,
        WaveLabel.WAVE_5,
        WaveLabel.A,
        WaveLabel.B,
        WaveLabel.C,
    )

    def __init__(self, targets: WaveTargetService | None = None) -> None:
        self._targets = targets or WaveTargetService()

    def project(self, context: MarketContextSnapshot, count: WaveCount) -> WaveProjection | None:
        if not count.sequence.waves:
            return None
        current = count.sequence.waves[-1].label
        try:
            next_wave = self._ORDER[self._ORDER.index(current) + 1]
        except (ValueError, IndexError):
            next_wave = WaveLabel.A
        expected = (
            0.618 if next_wave in (WaveLabel.WAVE_2, WaveLabel.WAVE_4, WaveLabel.B) else 1.618
        )
        return WaveProjection(
            next_wave,
            expected,
            self._targets.targets(context, next_wave, count.probability),
            count.confluence,
        )
