"""Pattern and canonical rule validation."""

from epip.elliott.models import WaveLabel, WavePattern, WaveSequence, WaveViolation
from epip.elliott.rules import ElliottRuleSet


class WaveValidator:
    def __init__(self, rules: ElliottRuleSet) -> None:
        self._rules = rules

    def validate(self, sequence: WaveSequence) -> tuple[WaveViolation, ...]:
        violations = list(self._rules.validate(sequence))
        labels = tuple(wave.label for wave in sequence.waves)
        expected: tuple[WaveLabel, ...] | None = None
        if sequence.pattern == WavePattern.IMPULSE:
            expected = (
                WaveLabel.WAVE_1,
                WaveLabel.WAVE_2,
                WaveLabel.WAVE_3,
                WaveLabel.WAVE_4,
                WaveLabel.WAVE_5,
            )
        elif sequence.pattern in (WavePattern.ABC, WavePattern.FLAT, WavePattern.ZIGZAG):
            expected = (WaveLabel.A, WaveLabel.B, WaveLabel.C)
        elif sequence.pattern == WavePattern.TRIANGLE:
            expected = (WaveLabel.A, WaveLabel.B, WaveLabel.C, WaveLabel.WAVE_4, WaveLabel.WAVE_5)
        elif sequence.pattern == WavePattern.DIAGONAL and len(labels) != 5:
            violations.append(WaveViolation("DIAGONAL", "Diagonal requires five waves"))
        if expected is not None and labels != expected:
            violations.append(WaveViolation("PATTERN", "Wave labels do not match pattern"))
        return tuple(violations)
