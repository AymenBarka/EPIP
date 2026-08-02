from epip.liquidity.config import LiquidityConfig
from epip.liquidity.equal_levels import EqualLevelDetector
from epip.liquidity.models import LiquiditySide
from epip.liquidity.pools import LiquidityPoolDetector
from tests.liquidity.helpers import sequence


def test_buy_and_sell_side_pools() -> None:
    highs, lows = EqualLevelDetector().detect(sequence(), LiquidityConfig())
    pools = LiquidityPoolDetector().detect(highs, lows, LiquidityConfig())
    assert {x.side for x in pools} == {LiquiditySide.BUY_SIDE, LiquiditySide.SELL_SIDE}
