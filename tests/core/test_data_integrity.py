"""Institutional data-integrity policy tests."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from math import inf, nan

import pytest

from epip.core import Candle, EventBus, Price
from epip.core.integrity import (
    EventIntegrityError,
    MissingFieldError,
    NumericIntegrityError,
    RelationshipIntegrityError,
    SerializationIntegrityError,
    VersionIntegrityError,
    require_finite,
    require_percentage,
    require_positive,
    require_text,
    require_unit_interval,
    require_version,
)
from epip.decision.models import DecisionConfidence, DecisionProbability, EntryZone
from epip.decision.serialization import from_dict as decision_from_dict
from epip.execution.events import OrderFilled
from epip.execution.models import Order, OrderFill, OrderSide, OrderState, OrderType
from epip.features.feature import Feature
from epip.fibonacci.models import (
    FibonacciDirection,
    FibonacciExtension,
    FibonacciRetracement,
    FibonacciSnapshot,
)
from epip.liquidity.fvg import FairValueGap
from epip.liquidity.models import LiquidityScope
from epip.portfolio.models import PortfolioPosition, PositionDirection
from epip.risk.models import Leverage, RiskLevel, RiskQuality, RiskScore


@pytest.mark.parametrize("value", (nan, inf, -inf))
def test_non_finite_values_are_rejected(value: float) -> None:
    with pytest.raises(NumericIntegrityError, match="finite"):
        require_finite(value, "value")
    with pytest.raises(NumericIntegrityError):
        Price(value)


@pytest.mark.parametrize(
    ("validator", "value"),
    (
        (require_positive, 0.0),
        (require_unit_interval, -0.01),
        (require_unit_interval, 1.01),
        (require_percentage, 100.01),
    ),
)
def test_numeric_boundaries_fail_fast(validator: object, value: float) -> None:
    with pytest.raises(NumericIntegrityError):
        validator(value, "value")  # type: ignore[operator]


def test_required_text_and_version_reject_corruption() -> None:
    with pytest.raises(MissingFieldError):
        require_text(" ", "id")
    with pytest.raises(VersionIntegrityError):
        require_version(0)
    with pytest.raises(VersionIntegrityError):
        require_version(True)


def test_candle_rejects_invalid_prices_volume_and_relationships() -> None:
    with pytest.raises(NumericIntegrityError):
        Candle("t", "EURUSD", "M1", 1.0, 2.0, 0.5, 1.5, nan)
    with pytest.raises(RelationshipIntegrityError):
        Candle("t", "EURUSD", "M1", 2.0, 1.0, 0.5, 1.5, 1.0)


def test_probability_objects_reject_instead_of_clamping() -> None:
    with pytest.raises(NumericIntegrityError):
        DecisionConfidence(1.1)
    with pytest.raises(NumericIntegrityError):
        DecisionProbability(nan)
    with pytest.raises(RelationshipIntegrityError):
        EntryZone(1.0, 2.0, 3.0)


def test_risk_scales_and_leverage_relationships() -> None:
    assert RiskScore(100.0, RiskQuality.HIGH, RiskLevel.LOW, 1.0).value == 100.0
    with pytest.raises(NumericIntegrityError):
        RiskScore(101.0, RiskQuality.HIGH, RiskLevel.LOW, 1.0)
    with pytest.raises(RelationshipIntegrityError):
        Leverage(11.0, 10.0)


def test_order_rejects_duplicate_fills_and_overfill() -> None:
    fill = OrderFill("fill", 1.0, 100.0, 0.0, "t")
    with pytest.raises(RelationshipIntegrityError, match="duplicated"):
        Order(
            "order",
            "plan",
            "EURUSD",
            OrderSide.BUY,
            OrderType.MARKET,
            2.0,
            100.0,
            None,
            None,
            OrderState.PARTIALLY_FILLED,
            (fill, fill),
        )
    with pytest.raises(RelationshipIntegrityError, match="exceeds"):
        Order(
            "order",
            "plan",
            "EURUSD",
            OrderSide.BUY,
            OrderType.MARKET,
            0.5,
            100.0,
            None,
            None,
            OrderState.FILLED,
            (fill,),
        )


def test_immutable_business_objects_remain_frozen() -> None:
    position = PortfolioPosition("EURUSD", 1.0, PositionDirection.LONG, 100.0, 101.0)
    with pytest.raises(FrozenInstanceError):
        position.quantity = 2.0  # type: ignore[misc]


def test_event_bus_rejects_invalid_payload_before_publication() -> None:
    class InvalidEvent:
        def validate_integrity(self) -> None:
            raise NumericIntegrityError("corrupted")

    bus = EventBus()
    with pytest.raises(EventIntegrityError, match="corrupted"):
        bus.publish(InvalidEvent())
    assert bus.event_history() == ()


def test_corrupted_serialization_uses_domain_exception() -> None:
    with pytest.raises(SerializationIntegrityError):
        decision_from_dict({})


def test_snapshot_probability_rejects_nan_and_out_of_range() -> None:
    retracement = FibonacciRetracement(1.0, 2.0, FibonacciDirection.BULLISH, ())
    extension = FibonacciExtension(1.0, 2.0, ())
    for probability in (nan, -0.1, 1.1):
        with pytest.raises(NumericIntegrityError):
            FibonacciSnapshot(
                "t",
                "EURUSD",
                "M1",
                1,
                FibonacciDirection.BULLISH,
                retracement,
                extension,
                (),
                probability=probability,
            )


def test_pipeline_dtos_validate_at_construction() -> None:
    with pytest.raises(MissingFieldError):
        Feature("", "name", "category", 1.0, "t", {}, 1.0, "source")
    with pytest.raises(NumericIntegrityError):
        Feature("id", "name", "category", 1.0, "t", {}, nan, "source")
    with pytest.raises(RelationshipIntegrityError):
        FairValueGap("EURUSD", "M1", "t", 2.0, 1.0, LiquidityScope.INTERNAL)


def test_event_payload_is_validated_before_publication() -> None:
    with pytest.raises(NumericIntegrityError):
        OrderFilled(
            id="event", timestamp="t", symbol="EURUSD", order_id="o", plan_id="p", quantity=nan
        )


def test_nested_mutable_payloads_are_deeply_frozen() -> None:
    source = {"nested": [1, {"value": 2}]}
    feature = Feature("id", "name", "category", source, "t", source, 1.0, "source")
    source["nested"].append(3)
    assert feature.value["nested"] == (1, {"value": 2})
    with pytest.raises(TypeError):
        feature.metadata["new"] = 1  # type: ignore[index]


def test_integrity_contract_rejects_arbitrary_objects() -> None:
    with pytest.raises(EventIntegrityError):
        EventBus().publish(object())
