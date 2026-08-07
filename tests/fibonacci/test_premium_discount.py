from epip.fibonacci.premium_discount import premium_discount


def test_premium_discount_equilibrium() -> None:
    premium, discount = premium_discount(1, 2, 0.5)
    assert premium.low == discount.high == 1.5
