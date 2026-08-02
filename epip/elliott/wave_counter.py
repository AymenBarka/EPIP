"""Deterministic primary Elliott count scoring."""

from epip.elliott.models import (
    CountStatus,
    WaveCount,
    WaveQuality,
    WaveSequence,
    WaveViolation,
)


class WaveCounter:
    def count(
        self,
        sequence: WaveSequence,
        violations: tuple[WaveViolation, ...],
        confluence: float,
    ) -> WaveCount:
        completeness = min(1.0, len(sequence.waves) / 5.0)
        penalty = min(0.8, len(violations) * 0.2)
        confidence = max(0.0, min(1.0, 0.55 * completeness + 0.45 * confluence - penalty))
        probability = max(0.0, min(1.0, 0.7 * confidence + 0.3 * confluence))
        quality = self._quality(confidence)
        status = CountStatus.INVALID if violations else CountStatus.VALID
        return WaveCount(
            "primary",
            sequence,
            violations,
            confidence,
            probability,
            quality,
            max(0.0, min(1.0, confluence)),
            status,
        )

    @staticmethod
    def _quality(score: float) -> WaveQuality:
        if score >= 0.85:
            return WaveQuality.VERY_HIGH
        if score >= 0.65:
            return WaveQuality.HIGH
        if score >= 0.4:
            return WaveQuality.MEDIUM
        if score >= 0.2:
            return WaveQuality.LOW
        return WaveQuality.VERY_LOW
