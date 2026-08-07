"""Deterministic alternate count generation."""

from dataclasses import replace

from epip.elliott.models import (
    AlternateCount,
    CountStatus,
    WaveCount,
    WaveLabel,
    WavePattern,
    WaveSequence,
)


class AlternateCounter:
    def generate(self, primary: WaveCount) -> tuple[AlternateCount, ...]:
        waves = primary.sequence.waves
        if len(waves) < 3:
            return ()
        relabeled = tuple(
            replace(wave, label=label)
            for wave, label in zip(waves[:3], (WaveLabel.A, WaveLabel.B, WaveLabel.C), strict=True)
        )
        sequence = WaveSequence(relabeled, WavePattern.ZIGZAG, primary.sequence.degree)
        count = replace(
            primary,
            count_id="alternate-1",
            sequence=sequence,
            probability=max(0.0, primary.probability * 0.75),
            confidence=max(0.0, primary.confidence * 0.8),
            status=CountStatus.ALTERNATE,
        )
        return (AlternateCount(count, "Three-wave corrective interpretation"),)
