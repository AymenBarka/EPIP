from epip.fibonacci.confluence import confluence_score
from tests.fibonacci.helpers import inputs


def test_liquidity_confluence_bounded() -> None:
    swings, market_structure, liquidity = inputs()
    assert 0 <= confluence_score(market_structure, liquidity, swings) <= 1
