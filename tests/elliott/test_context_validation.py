from epip.elliott.validators import FibonacciWaveValidator, LiquidityTerminationValidator
from tests.elliott.helpers import market_context


def test_official_fibonacci_and_liquidity_evidence_is_consumed() -> None:
    context = market_context(score=0.8)
    assert FibonacciWaveValidator().score(context) == 0.8
    assert LiquidityTerminationValidator().score(context) == 0.8


def test_missing_liquidity_has_zero_termination_score() -> None:
    from dataclasses import replace

    context = market_context()
    aggregate = replace(context.context, current_liquidity_pools=())
    assert LiquidityTerminationValidator().score(replace(context, context=aggregate)) == 0.0
