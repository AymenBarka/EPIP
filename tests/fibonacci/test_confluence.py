from epip.fibonacci.confluence import confluence_score
from tests.fibonacci.helpers import inputs


def test_liquidity_confluence_bounded() -> None:
    s, m, l = inputs()
    assert 0 <= confluence_score(m, l, s) <= 1
