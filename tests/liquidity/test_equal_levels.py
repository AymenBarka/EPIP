from epip.liquidity.config import LiquidityConfig
from epip.liquidity.equal_levels import EqualLevelDetector
from tests.liquidity.helpers import sequence


def test_equal_highs_and_lows() -> None:
    highs, lows = EqualLevelDetector().detect(sequence(), LiquidityConfig())
    assert len(highs) == len(lows) == 1
