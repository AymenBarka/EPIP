"""Portfolio engine configuration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class PortfolioConfig:
    initial_capital: float = 100_000.0
    margin_rate: float = 0.20
    max_gross_exposure: float = 2.0
    max_net_exposure: float = 1.0
    max_symbol_allocation: float = 0.25
    max_correlation_allocation: float = 0.50
    max_drawdown: float = 0.20
    correlation_groups: tuple[tuple[str, tuple[str, ...]], ...] = ()
    engine_version: str = "EPIP-015"
