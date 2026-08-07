from epip.context.aggregator import MarketContextAggregator
from tests.context.helpers import official_inputs


def test_confluence_is_deterministic_and_bounded() -> None:
    _, structure, liquidity, fibonacci = official_inputs(score=1.0)
    result = MarketContextAggregator().confluence(structure, liquidity, fibonacci)
    assert result.score == 1.0
    assert result == MarketContextAggregator().confluence(structure, liquidity, fibonacci)
    _, structure, liquidity, fibonacci = official_inputs(score=0.0)
    assert MarketContextAggregator().confluence(structure, liquidity, fibonacci).score == 0.0
