"""Canonical modular Elliott rules."""

from collections.abc import Callable
from dataclasses import dataclass

from epip.elliott.models import WaveLabel, WaveRule, WaveSequence, WaveViolation

RuleCheck = Callable[[WaveSequence], tuple[WaveViolation, ...]]


@dataclass(frozen=True, slots=True)
class ElliottRuleSet:
    rules: tuple[tuple[WaveRule, RuleCheck], ...]

    def validate(self, sequence: WaveSequence) -> tuple[WaveViolation, ...]:
        return tuple(violation for _, check in self.rules for violation in check(sequence))


def wave_two_origin(sequence: WaveSequence) -> tuple[WaveViolation, ...]:
    waves = {wave.label: wave for wave in sequence.waves}
    first, second = waves.get(WaveLabel.WAVE_1), waves.get(WaveLabel.WAVE_2)
    if first is None or second is None:
        return ()
    invalid = (
        second.end_price < first.start_price
        if first.end_price >= first.start_price
        else second.end_price > first.start_price
    )
    return (
        (WaveViolation("W2_ORIGIN", "Wave 2 retraces beyond Wave 1 origin", WaveLabel.WAVE_2),)
        if invalid
        else ()
    )


def wave_three_not_shortest(sequence: WaveSequence) -> tuple[WaveViolation, ...]:
    waves = {wave.label: wave for wave in sequence.waves}
    impulse = [waves.get(label) for label in (WaveLabel.WAVE_1, WaveLabel.WAVE_3, WaveLabel.WAVE_5)]
    if any(wave is None for wave in impulse):
        return ()
    first, third, fifth = impulse
    assert first is not None and third is not None and fifth is not None
    return (
        (WaveViolation("W3_SHORTEST", "Wave 3 is the shortest impulse wave", WaveLabel.WAVE_3),)
        if third.length < min(first.length, fifth.length)
        else ()
    )


def wave_four_overlap(sequence: WaveSequence) -> tuple[WaveViolation, ...]:
    waves = {wave.label: wave for wave in sequence.waves}
    first, fourth = waves.get(WaveLabel.WAVE_1), waves.get(WaveLabel.WAVE_4)
    if first is None or fourth is None:
        return ()
    low, high = sorted((first.start_price, first.end_price))
    overlap = low <= fourth.end_price <= high
    return (
        (WaveViolation("W4_OVERLAP", "Wave 4 overlaps Wave 1", WaveLabel.WAVE_4),)
        if overlap
        else ()
    )


def canonical_rules(*, allow_diagonal_overlap: bool = False) -> ElliottRuleSet:
    rules: list[tuple[WaveRule, RuleCheck]] = [
        (WaveRule("W2_ORIGIN", "Wave 2 never exceeds Wave 1 origin"), wave_two_origin),
        (WaveRule("W3_SHORTEST", "Wave 3 is never shortest"), wave_three_not_shortest),
    ]
    if not allow_diagonal_overlap:
        rules.append(
            (
                WaveRule("W4_OVERLAP", "Wave 4 never overlaps Wave 1", True),
                wave_four_overlap,
            )
        )
    return ElliottRuleSet(tuple(rules))
