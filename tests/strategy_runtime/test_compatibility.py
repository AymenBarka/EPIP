from inspect import signature

from epip.decision import DecisionSnapshot
from epip.execution import ExecutionSnapshot
from epip.execution.protocols import ExecutionEngineProtocol
from epip.portfolio import PortfolioSnapshot
from epip.portfolio.protocols import PortfolioEngineProtocol
from epip.risk import PositionPlan
from epip.risk.protocols import RiskEngineProtocol


def test_legacy_public_apis_remain_distinct_and_unchanged() -> None:
    assert tuple(signature(RiskEngineProtocol.process).parameters) == (
        "self",
        "decision",
        "market_data",
    )
    assert tuple(signature(ExecutionEngineProtocol.execute).parameters) == (
        "self",
        "plan",
        "timestamp",
        "observations",
    )
    assert tuple(signature(PortfolioEngineProtocol.process).parameters) == ("self", "execution")
    assert len({DecisionSnapshot, PositionPlan, ExecutionSnapshot, PortfolioSnapshot}) == 4
