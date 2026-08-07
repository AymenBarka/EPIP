"""Deterministic wave degree selection."""

from typing import ClassVar

from epip.elliott.models import WaveDegree


class WaveDegreeDetector:
    _MAP: ClassVar[dict[str, WaveDegree]] = {
        "D1": WaveDegree.PRIMARY,
        "H4": WaveDegree.INTERMEDIATE,
        "H1": WaveDegree.MINOR,
        "M15": WaveDegree.MINUTE,
        "M5": WaveDegree.MINUETTE,
        "M1": WaveDegree.SUBMINUETTE,
    }

    def detect(self, timeframe: str, fallback: WaveDegree) -> WaveDegree:
        return self._MAP.get(timeframe, fallback)
