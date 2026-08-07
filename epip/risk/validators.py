"""Risk input and configuration validation."""

from epip.decision.models import DecisionAction, DecisionSnapshot
from epip.risk.config import RiskConfig
from epip.risk.exceptions import InvalidRiskInputError


def validate_config(config: RiskConfig) -> None:
    if config.account_equity <= 0 or config.available_margin < 0:
        raise InvalidRiskInputError("equity must be positive and margin non-negative")
    if not 0 < config.profile.risk_fraction <= config.limits.max_risk_per_trade <= 1:
        raise InvalidRiskInputError("risk fractions must be in range and within limits")
    if config.max_leverage <= 0 or config.min_position_size < 0:
        raise InvalidRiskInputError("invalid leverage or minimum position")


def validate_decision(snapshot: DecisionSnapshot) -> None:
    decision = snapshot.decision
    if decision.action not in (DecisionAction.LONG, DecisionAction.SHORT):
        raise InvalidRiskInputError("only LONG and SHORT decisions can be planned")
    if decision.entry_zone is None or decision.entry_zone.suggested_price <= 0:
        raise InvalidRiskInputError("decision requires a positive entry price")
