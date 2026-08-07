"""Risk engine configuration."""

from dataclasses import dataclass, field

from epip.risk.models import RiskProfile, SizingMethod


@dataclass(frozen=True, slots=True)
class PortfolioLimits:
    max_risk_per_trade: float = 0.02
    max_daily_loss: float = 0.03
    max_weekly_loss: float = 0.06
    max_monthly_loss: float = 0.10
    max_positions: int = 10
    max_symbol_exposure: float = 0.50
    max_correlated_exposure: float = 0.50


@dataclass(frozen=True, slots=True)
class RiskConfig:
    profile: RiskProfile = field(default_factory=lambda: RiskProfile(SizingMethod.FIXED_RISK, 0.01))
    limits: PortfolioLimits = field(default_factory=PortfolioLimits)
    account_equity: float = 100_000.0
    available_margin: float = 100_000.0
    max_leverage: float = 5.0
    min_position_size: float = 0.0
    max_position_notional: float = 100_000.0
    atr_multiplier: float = 2.0
    volatility_target: float = 0.01
    trailing_stop: bool = False
    break_even_trigger: float | None = None
    engine_version: str = "EPIP-013"
