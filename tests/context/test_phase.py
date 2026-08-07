import pytest

from epip.context.aggregator import MarketContextAggregator
from epip.context.snapshot import MarketPhase
from epip.market_structure.models import StructureState, TrendDirection
from tests.context.helpers import official_inputs


@pytest.mark.parametrize(
    ("state", "expected"),
    (
        (StructureState.UNKNOWN, MarketPhase.UNKNOWN),
        (StructureState.ACCUMULATION, MarketPhase.ACCUMULATION),
        (StructureState.UPTREND, MarketPhase.MARKUP),
        (StructureState.DISTRIBUTION, MarketPhase.DISTRIBUTION),
        (StructureState.DOWNTREND, MarketPhase.MARKDOWN),
        (StructureState.RANGE, MarketPhase.RANGE),
    ),
)
def test_market_phase(state: StructureState, expected: MarketPhase) -> None:
    _, structure, _, _ = official_inputs(direction=TrendDirection.RANGE, state=state)
    assert MarketContextAggregator().phase(structure) == expected
