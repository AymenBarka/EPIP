"""Application service orchestrating Elliott analysis."""

from epip.context import MarketContextSnapshot
from epip.elliott.alternate_counter import AlternateCounter
from epip.elliott.config import ElliottConfig
from epip.elliott.models import ElliottAnalysis
from epip.elliott.projection import WaveProjectionService
from epip.elliott.rules import canonical_rules
from epip.elliott.validators import FibonacciWaveValidator, LiquidityTerminationValidator
from epip.elliott.wave_counter import WaveCounter
from epip.elliott.wave_detector import WaveDetector
from epip.elliott.wave_validator import WaveValidator


class ElliottAnalyzer:
    def __init__(self, config: ElliottConfig) -> None:
        self._config = config
        self._detector = WaveDetector()
        self._validator = WaveValidator(
            canonical_rules(allow_diagonal_overlap=config.allow_diagonal_overlap)
        )
        self._counter = WaveCounter()
        self._alternates = AlternateCounter()
        self._projection = WaveProjectionService()
        self._fibonacci = FibonacciWaveValidator()
        self._liquidity = LiquidityTerminationValidator()

    def analyze(self, context: MarketContextSnapshot) -> ElliottAnalysis:
        sequence = self._detector.detect(context, self._config.default_degree)
        violations = self._validator.validate(sequence)
        confluence = (
            context.context.confluence_score
            + self._fibonacci.score(context)
            + self._liquidity.score(context)
        ) / 3.0
        primary = self._counter.count(sequence, violations, confluence)
        return ElliottAnalysis(
            primary,
            self._alternates.generate(primary),
            self._projection.project(context, primary),
        )
