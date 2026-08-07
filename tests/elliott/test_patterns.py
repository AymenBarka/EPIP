import pytest

from epip.elliott.degree_detector import WaveDegreeDetector
from epip.elliott.models import WaveDegree, WaveLabel, WavePattern, WaveSequence
from epip.elliott.rules import canonical_rules
from epip.elliott.wave_detector import WaveDetector
from epip.elliott.wave_validator import WaveValidator
from tests.elliott.helpers import market_context


def test_detector_finds_impulse_and_abc() -> None:
    detector = WaveDetector()
    impulse = detector.detect(market_context(), WaveDegree.MINOR)
    abc = detector.detect(market_context((1.0, 2.0, 1.5, 2.5)), WaveDegree.MINOR)
    assert impulse.pattern == WavePattern.IMPULSE
    assert tuple(wave.label for wave in impulse.waves) == tuple(
        WaveLabel(str(index)) for index in range(1, 6)
    )
    assert abc.pattern == WavePattern.ABC


@pytest.mark.parametrize(
    "pattern",
    (WavePattern.ABC, WavePattern.FLAT, WavePattern.ZIGZAG),
)
def test_corrective_patterns_validate(pattern: WavePattern) -> None:
    detected = WaveDetector().detect(market_context((1.0, 2.0, 1.5, 2.5)), WaveDegree.MINOR)
    sequence = WaveSequence(detected.waves, pattern, detected.degree)
    assert WaveValidator(canonical_rules()).validate(sequence) == ()


def test_degree_detector_supports_all_declared_degrees() -> None:
    detector = WaveDegreeDetector()
    assert detector.detect("D1", WaveDegree.CYCLE) == WaveDegree.PRIMARY
    assert detector.detect("H4", WaveDegree.CYCLE) == WaveDegree.INTERMEDIATE
    assert detector.detect("H1", WaveDegree.CYCLE) == WaveDegree.MINOR
    assert detector.detect("M15", WaveDegree.CYCLE) == WaveDegree.MINUTE
    assert detector.detect("M5", WaveDegree.CYCLE) == WaveDegree.MINUETTE
    assert detector.detect("M1", WaveDegree.CYCLE) == WaveDegree.SUBMINUETTE
    assert detector.detect("W1", WaveDegree.GRAND_SUPERCYCLE) == WaveDegree.GRAND_SUPERCYCLE
