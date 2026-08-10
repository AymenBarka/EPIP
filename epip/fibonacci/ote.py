from epip.fibonacci.models import FibonacciDirection, GoldenZone, OTEZone


def ote_zones(
    start: float,
    end: float,
    direction: FibonacciDirection,
    ote_low: float,
    ote_high: float,
    golden_low: float,
    golden_high: float,
    score: float,
) -> tuple[OTEZone, GoldenZone]:
    distance = abs(end - start)

    def price(ratio: float) -> float:
        return (
            end - distance * ratio
            if direction == FibonacciDirection.BULLISH
            else end + distance * ratio
        )

    ote_prices = sorted((price(ote_low), price(ote_high)))
    golden_prices = sorted((price(golden_low), price(golden_high)))
    return OTEZone(ote_prices[0], ote_prices[1], "OTE", score), GoldenZone(
        golden_prices[0], golden_prices[1], "GOLDEN", score
    )
