from dataclasses import replace

from epip.elliott.models import WaveDegree, WaveLabel, WavePattern, WaveSequence
from epip.elliott.rules import canonical_rules
from epip.elliott.wave_detector import WaveDetector
from epip.elliott.wave_validator import WaveValidator
from tests.elliott.helpers import market_context


def _impulse() -> WaveSequence:
    return WaveDetector().detect(market_context(), WaveDegree.MINOR)


def test_wave_two_never_exceeds_origin() -> None:
    sequence = _impulse()
    waves = list(sequence.waves)
    waves[1] = replace(waves[1], end_price=0.5)
    violations = WaveValidator(canonical_rules()).validate(replace(sequence, waves=tuple(waves)))
    assert any(item.rule_id == "W2_ORIGIN" for item in violations)


def test_wave_three_is_never_shortest() -> None:
    sequence = _impulse()
    waves = list(sequence.waves)
    waves[2] = replace(waves[2], start_price=1.5, end_price=1.6)
    violations = WaveValidator(canonical_rules()).validate(replace(sequence, waves=tuple(waves)))
    assert any(item.rule_id == "W3_SHORTEST" for item in violations)


def test_wave_four_overlap_configurable_for_diagonal() -> None:
    sequence = _impulse()
    waves = list(sequence.waves)
    waves[3] = replace(waves[3], end_price=1.8)
    overlap = replace(sequence, waves=tuple(waves), pattern=WavePattern.DIAGONAL)
    strict = WaveValidator(canonical_rules()).validate(overlap)
    diagonal = WaveValidator(canonical_rules(allow_diagonal_overlap=True)).validate(overlap)
    assert any(item.rule_id == "W4_OVERLAP" for item in strict)
    assert not any(item.rule_id == "W4_OVERLAP" for item in diagonal)


def test_triangle_and_diagonal_validation() -> None:
    impulse = _impulse()
    triangle_labels = (WaveLabel.A, WaveLabel.B, WaveLabel.C, WaveLabel.WAVE_4, WaveLabel.WAVE_5)
    triangle = WaveSequence(
        tuple(
            replace(wave, label=label)
            for wave, label in zip(impulse.waves, triangle_labels, strict=True)
        ),
        WavePattern.TRIANGLE,
        impulse.degree,
    )
    validator = WaveValidator(canonical_rules(allow_diagonal_overlap=True))
    assert not any(item.rule_id == "PATTERN" for item in validator.validate(triangle))
    diagonal = replace(triangle, pattern=WavePattern.DIAGONAL, waves=triangle.waves[:3])
    assert any(item.rule_id == "DIAGONAL" for item in validator.validate(diagonal))
