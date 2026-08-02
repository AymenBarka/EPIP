from epip.fibonacci.models import DiscountZone, PremiumZone


def premium_discount(start: float, end: float, score: float) -> tuple[PremiumZone, DiscountZone]:
    low, high = sorted((start, end))
    mid = (low + high) / 2
    return PremiumZone(mid, high, "PREMIUM", score), DiscountZone(low, mid, "DISCOUNT", score)
