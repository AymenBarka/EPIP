from epip.context.builder import MarketContextBuilder
from tests.context.helpers import official_inputs


def test_builder_reuses_official_snapshots() -> None:
    inputs = official_inputs()
    context = MarketContextBuilder().build(*inputs)
    assert context.swing_snapshot is inputs[0]
    assert context.structure_snapshot is inputs[1]
    assert context.liquidity_snapshot is inputs[2]
    assert context.fibonacci_snapshot is inputs[3]
    assert context.current_liquidity_pools == inputs[2].pools
    assert context.ote is not None and context.golden_zone is not None
