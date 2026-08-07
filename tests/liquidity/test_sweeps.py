from epip.liquidity.config import LiquidityConfig
from epip.liquidity.equal_levels import EqualLevelDetector
from epip.liquidity.pools import LiquidityPoolDetector
from epip.liquidity.sweeps import LiquiditySweepDetector
from tests.liquidity.helpers import sequence


def test_confirmed_and_false_sweep() -> None:
    cfg = LiquidityConfig()
    highs, lows = EqualLevelDetector().detect(sequence(), cfg)
    pools = LiquidityPoolDetector().detect(highs, lows, cfg)
    assert LiquiditySweepDetector().detect(sequence(1.21), pools, cfg)[0].confirmed
    assert not LiquiditySweepDetector().detect(sequence(1.15), pools, cfg)
