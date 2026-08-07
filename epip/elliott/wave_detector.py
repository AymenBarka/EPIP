"""Wave segmentation using only Market Context swings."""

from epip.context import MarketContextSnapshot
from epip.elliott.degree_detector import WaveDegreeDetector
from epip.elliott.models import Wave, WaveDegree, WaveLabel, WavePattern, WaveSequence


class WaveDetector:
    def __init__(self, degree_detector: WaveDegreeDetector | None = None) -> None:
        self._degree_detector = degree_detector or WaveDegreeDetector()

    def detect(self, context: MarketContextSnapshot, fallback: WaveDegree) -> WaveSequence:
        swings = context.context.swing_snapshot.swings
        degree = self._degree_detector.detect(context.timeframe, fallback)
        count = min(max(len(swings) - 1, 0), 5)
        if count >= 5:
            labels: tuple[WaveLabel, ...] = (
                WaveLabel.WAVE_1,
                WaveLabel.WAVE_2,
                WaveLabel.WAVE_3,
                WaveLabel.WAVE_4,
                WaveLabel.WAVE_5,
            )
            pattern = WavePattern.IMPULSE
        elif count >= 3:
            labels = (WaveLabel.A, WaveLabel.B, WaveLabel.C)
            pattern = WavePattern.ABC
            count = 3
        else:
            labels = (WaveLabel.WAVE_1, WaveLabel.WAVE_2)[:count]
            pattern = WavePattern.UNKNOWN
        waves = tuple(
            Wave(
                labels[index],
                degree,
                swings[index].point.index,
                swings[index + 1].point.index,
                swings[index].point.timestamp,
                swings[index + 1].point.timestamp,
                swings[index].point.price,
                swings[index + 1].point.price,
                "UP" if swings[index + 1].point.price >= swings[index].point.price else "DOWN",
            )
            for index in range(count)
        )
        return WaveSequence(waves, pattern, degree)
