"""Immutable Portfolio projection consumed by the future Capital Risk boundary."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime._base import (
    CONTRACT_VERSION,
    digest,
    finite,
    require_digest,
    text,
    timestamp,
)


@dataclass(frozen=True, slots=True)
class PortfolioRiskView:
    contract_version: str
    view_id: str
    portfolio_version: int
    as_of_timestamp: str
    base_currency: str
    equity: float
    available_capital: float
    used_margin: float
    gross_exposure: float
    net_exposure: float
    instrument_exposure: float
    open_risk_amount: float | None
    current_leverage: float | None
    drawdown_fraction: float
    open_position_count: int
    correlation_exposure: tuple[tuple[str, float], ...]
    limit_facts: tuple[str, ...]
    source_execution_version: int
    source_digest: str

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported portfolio-risk contract version")
        if type(self.portfolio_version) is not int or self.portfolio_version < 0:
            raise DataIntegrityError("portfolio_version must be non-negative")
        if type(self.source_execution_version) is not int or self.source_execution_version < 0:
            raise DataIntegrityError("source_execution_version must be non-negative")
        if type(self.open_position_count) is not int or self.open_position_count < 0:
            raise DataIntegrityError("open_position_count must be non-negative")
        object.__setattr__(
            self, "as_of_timestamp", timestamp(self.as_of_timestamp, "as_of_timestamp")
        )
        object.__setattr__(self, "base_currency", text(self.base_currency, "base_currency"))
        for name in (
            "equity",
            "available_capital",
            "used_margin",
            "gross_exposure",
            "instrument_exposure",
            "drawdown_fraction",
        ):
            object.__setattr__(self, name, finite(getattr(self, name), name, non_negative=True))
        object.__setattr__(self, "net_exposure", finite(self.net_exposure, "net_exposure"))
        if self.open_risk_amount is not None:
            object.__setattr__(
                self,
                "open_risk_amount",
                finite(self.open_risk_amount, "open_risk_amount", non_negative=True),
            )
        if self.current_leverage is not None:
            object.__setattr__(
                self,
                "current_leverage",
                finite(self.current_leverage, "current_leverage", non_negative=True),
            )
        if self.drawdown_fraction > 1.0:
            raise DataIntegrityError("drawdown_fraction must not exceed 1")
        if type(self.correlation_exposure) is not tuple:
            raise DataIntegrityError("correlation_exposure must be a tuple")
        correlations = tuple(
            sorted(
                (text(key, "correlation key"), finite(value, "correlation"))
                for key, value in self.correlation_exposure
            )
        )
        if len({key for key, _ in correlations}) != len(correlations):
            raise DataIntegrityError("correlation keys must be unique")
        object.__setattr__(self, "correlation_exposure", correlations)
        if type(self.limit_facts) is not tuple or any(
            type(item) is not str for item in self.limit_facts
        ):
            raise DataIntegrityError("limit_facts must be a tuple of strings")
        object.__setattr__(self, "limit_facts", tuple(sorted(set(self.limit_facts))))
        object.__setattr__(
            self, "source_digest", require_digest(self.source_digest, "source_digest")
        )
        if self.view_id != digest(self, exclude=frozenset({"view_id"})):
            raise DataIntegrityError("view_id does not match canonical portfolio risk content")
