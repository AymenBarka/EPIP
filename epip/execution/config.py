"""Execution engine configuration."""

from dataclasses import dataclass

from epip.execution.models import CommissionMode, OrderType, SlippageMode


@dataclass(frozen=True, slots=True)
class ExecutionConfig:
    default_order_type: OrderType = OrderType.MARKET
    slippage_mode: SlippageMode = SlippageMode.FIXED
    slippage_value: float = 0.0
    commission_mode: CommissionMode = CommissionMode.FIXED
    commission_value: float = 0.0
    max_retries: int = 2
    retryable_messages: tuple[str, ...] = ("TEMPORARY", "TIMEOUT")
    engine_version: str = "EPIP-014"
