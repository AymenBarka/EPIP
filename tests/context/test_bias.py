from epip.context.aggregator import MarketContextAggregator
from epip.context.snapshot import InstitutionalBias
from epip.market_structure.models import TrendDirection


def test_bull_bear_range_bias() -> None:
    aggregator = MarketContextAggregator()
    assert aggregator.bias(TrendDirection.UPTREND, 0.8).bias == InstitutionalBias.STRONGLY_BULLISH
    assert aggregator.bias(TrendDirection.UPTREND, 0.4).bias == InstitutionalBias.BULLISH
    assert aggregator.bias(TrendDirection.DOWNTREND, 0.8).bias == InstitutionalBias.STRONGLY_BEARISH
    assert aggregator.bias(TrendDirection.DOWNTREND, 0.4).bias == InstitutionalBias.BEARISH
    assert aggregator.bias(TrendDirection.RANGE, 1.0).bias == InstitutionalBias.NEUTRAL
