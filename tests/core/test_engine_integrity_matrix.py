"""Acceptance matrix for every official engine integrity boundary."""

from collections.abc import Callable
from dataclasses import dataclass

import pytest

from epip.context.engine import MarketContextEngine
from epip.core.integrity import NumericIntegrityError, integrity_boundary
from epip.core.kernel import Kernel
from epip.decision.engine import DecisionEngine
from epip.elliott.engine import ElliottWaveEngine
from epip.execution.engine import ExecutionEngine
from epip.fibonacci.engine import FibonacciEngine
from epip.liquidity.engine import LiquidityEngine
from epip.market_structure.engine import MarketStructureEngine
from epip.marketdata.datasource import DataSource
from epip.portfolio.engine import PortfolioEngine
from epip.replay.replay_engine import ReplayEngine
from epip.risk.engine import RiskEngine
from epip.swing.engine import SwingEngine


@dataclass(frozen=True, slots=True)
class _InvalidBoundaryObject:
    probability: float = float("nan")


ENGINE_BOUNDARIES: tuple[tuple[str, Callable[..., object]], ...] = (
    ("core", Kernel.run),
    ("marketdata", DataSource.history),
    ("replay", ReplayEngine.run),
    ("swing", SwingEngine.process_candle),
    ("market_structure", MarketStructureEngine.process_sequence),
    ("liquidity", LiquidityEngine.process),
    ("fibonacci", FibonacciEngine.process),
    ("context", MarketContextEngine.process),
    ("elliott", ElliottWaveEngine.process),
    ("decision", DecisionEngine.process),
    ("risk", RiskEngine.process),
    ("execution", ExecutionEngine.execute),
    ("portfolio", PortfolioEngine.process),
)


@pytest.mark.parametrize(("domain", "boundary"), ENGINE_BOUNDARIES)
def test_every_engine_rejects_invalid_domain_input(
    domain: str, boundary: Callable[..., object]
) -> None:
    assert getattr(boundary, "__integrity_boundary__", False), domain
    with pytest.raises(NumericIntegrityError):
        boundary(object(), _InvalidBoundaryObject())


@pytest.mark.parametrize(("domain", "boundary"), ENGINE_BOUNDARIES)
def test_every_engine_uses_the_output_integrity_guard(
    domain: str, boundary: Callable[..., object]
) -> None:
    assert getattr(boundary, "__integrity_boundary__", False), domain


def test_integrity_boundary_rejects_invalid_engine_output() -> None:
    @integrity_boundary
    def invalid_output() -> _InvalidBoundaryObject:
        return _InvalidBoundaryObject()

    with pytest.raises(NumericIntegrityError):
        invalid_output()
