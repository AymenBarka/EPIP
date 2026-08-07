"""Portfolio boundary validation."""

from epip.execution.models import ExecutionSnapshot, OrderState
from epip.portfolio.config import PortfolioConfig
from epip.portfolio.exceptions import InvalidPortfolioInputError


def validate_config(config: PortfolioConfig) -> None:
    if config.initial_capital <= 0 or not 0 <= config.margin_rate <= 1:
        raise InvalidPortfolioInputError("capital must be positive and margin rate bounded")
    limits = (
        config.max_gross_exposure,
        config.max_net_exposure,
        config.max_symbol_allocation,
        config.max_correlation_allocation,
        config.max_drawdown,
    )
    if any(limit <= 0 for limit in limits):
        raise InvalidPortfolioInputError("portfolio limits must be positive")


def validate_execution(snapshot: ExecutionSnapshot) -> None:
    report = snapshot.report
    if not report.completed or report.order.state != OrderState.FILLED:
        raise InvalidPortfolioInputError("Portfolio consumes completed FILLED executions only")
    if report.filled_quantity <= 0 or report.average_fill_price is None:
        raise InvalidPortfolioInputError("execution requires positive fill quantity and price")
