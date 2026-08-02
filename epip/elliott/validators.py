"""Market Context, Fibonacci, and liquidity evidence validation."""

from epip.context import MarketContextSnapshot


class ElliottInputValidator:
    def validate(self, context: MarketContextSnapshot) -> bool:
        aggregate = context.context
        return (
            aggregate.symbol == context.symbol
            and aggregate.timeframe == context.timeframe
            and context.version.context > 0
            and context.version.fibonacci == aggregate.fibonacci_snapshot.version
            and context.version.liquidity == aggregate.liquidity_snapshot.version
        )


class FibonacciWaveValidator:
    def score(self, context: MarketContextSnapshot) -> float:
        fibonacci = context.context.fibonacci_snapshot
        return max(0.0, min(1.0, (fibonacci.confluence_score + fibonacci.probability) / 2.0))


class LiquidityTerminationValidator:
    def score(self, context: MarketContextSnapshot) -> float:
        pools = context.context.current_liquidity_pools
        if not pools:
            return 0.0
        return max(0.0, min(1.0, max(pool.confluence_score for pool in pools)))
