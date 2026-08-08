"""Institutional determinism and identity contract tests."""

from __future__ import annotations

from datetime import timedelta
from typing import cast

import pytest

from epip.core import (
    BaseEvent,
    Candle,
    Decision,
    DeterministicClock,
    DeterministicIdGenerator,
    Evidence,
    MarketContext,
    Price,
    SystemClock,
    SystemIdGenerator,
)
from epip.core.types import DecisionType, Direction


def test_deterministic_clock_is_explicit_and_repeatable() -> None:
    clock = DeterministicClock("2025-01-01T00:00:00Z")
    assert clock.now() == "2025-01-01T00:00:00+00:00"
    assert clock.advance(timedelta(seconds=5)) == "2025-01-01T00:00:05+00:00"
    clock.set("2025-01-02T00:00:00")
    assert clock.now() == "2025-01-02T00:00:00+00:00"


def test_deterministic_clock_normalizes_offsets() -> None:
    clock = DeterministicClock("2025-01-01T01:00:00+01:00")
    assert clock.now() == "2025-01-01T00:00:00+00:00"


def test_deterministic_generators_reproduce_sequences() -> None:
    first = DeterministicIdGenerator("seed")
    second = DeterministicIdGenerator("seed")
    sequence_one = [first.generate("event", "EURUSD") for _ in range(3)]
    sequence_two = [second.generate("event", "EURUSD") for _ in range(3)]
    assert sequence_one == sequence_two
    assert len(set(sequence_one)) == 3
    first.reset()
    assert first.generate("event", "EURUSD") == sequence_one[0]


def test_different_seeds_produce_different_identities() -> None:
    assert DeterministicIdGenerator("a").generate("event") != DeterministicIdGenerator(
        "b"
    ).generate("event")


def test_system_services_satisfy_public_contracts() -> None:
    assert "+00:00" in SystemClock().now()
    assert len(SystemIdGenerator().generate("test")) == 32


def test_same_services_produce_byte_identical_serialization() -> None:
    def build() -> str:
        return Candle(
            timestamp="2025-01-01T00:00:00Z",
            symbol="EURUSD",
            timeframe="M1",
            open=1.1,
            high=1.2,
            low=1.0,
            close=1.15,
            volume=10.0,
            clock=DeterministicClock("2025-01-01T00:00:01Z"),
            id_generator=DeterministicIdGenerator("replay"),
        ).to_json()

    assert build().encode() == build().encode()


def test_serialization_round_trip_preserves_identity() -> None:
    candle = Candle(
        timestamp="2025-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.1,
        high=1.2,
        low=1.0,
        close=1.15,
        volume=10.0,
        clock=DeterministicClock(),
        id_generator=DeterministicIdGenerator(),
    )
    restored = Candle.from_json(candle.to_json())
    assert restored == candle
    assert restored.uuid == candle.uuid
    assert restored.created_at == candle.created_at
    assert restored.to_json() == candle.to_json()


def test_technical_metadata_does_not_affect_business_equality() -> None:
    first = BaseEvent(id="event", timestamp="2025-01-01T00:00:00Z", created_at="a", uuid="one")
    second = BaseEvent(
        id="event",
        timestamp="2025-01-01T00:00:00Z",
        created_at="b",
        uuid="two",
        schema_version=99,
    )
    assert first == second
    assert hash(first) == hash(second)


def test_event_identity_is_deterministic_and_unique() -> None:
    ids = DeterministicIdGenerator("events")
    clock = DeterministicClock("2025-01-01T00:00:00Z")
    first = BaseEvent(id="one", timestamp="t", clock=clock, id_generator=ids)
    second = BaseEvent(id="two", timestamp="t", clock=clock, id_generator=ids)
    assert first.created_at == second.created_at
    assert first.uuid != second.uuid
    assert first.schema_version == second.schema_version == 1


def test_different_clocks_are_observable() -> None:
    first = BaseEvent(id="event", timestamp="t", clock=DeterministicClock("2020-01-01T00:00:00Z"))
    second = BaseEvent(id="event", timestamp="t", clock=DeterministicClock("2021-01-01T00:00:00Z"))
    assert first.created_at != second.created_at
    assert first == second


def test_numeric_identity_is_immutable_and_round_trips() -> None:
    price = Price(
        1.25,
        clock=DeterministicClock(),
        id_generator=DeterministicIdGenerator("price"),
    )
    restored = Price.from_json(price.to_json())
    assert restored == price
    assert restored.uuid == price.uuid
    with pytest.raises(AttributeError):
        price.uuid = "changed"


def test_candle_propagates_identity_services_to_prices() -> None:
    def build() -> Candle:
        return Candle(
            timestamp="2025-01-01T00:00:00Z",
            symbol="EURUSD",
            timeframe="M1",
            open=1.0,
            high=1.2,
            low=0.9,
            close=1.1,
            volume=1.0,
            clock=DeterministicClock(),
            id_generator=DeterministicIdGenerator("prices"),
        )

    first, second = build(), build()
    first_prices = tuple(
        cast(Price, item) for item in (first.open, first.high, first.low, first.close)
    )
    second_prices = tuple(
        cast(Price, item) for item in (second.open, second.high, second.low, second.close)
    )
    assert tuple(item.uuid for item in first_prices) == tuple(item.uuid for item in second_prices)


def test_runtime_metadata_does_not_affect_business_equality() -> None:
    evidence_one = Evidence(
        "evidence",
        "source",
        "category",
        Direction.BUY,
        0.8,
        "timestamp",
        metadata={"runtime": 1},
        created_at="one",
        uuid="one",
    )
    evidence_two = Evidence(
        "evidence",
        "source",
        "category",
        Direction.BUY,
        0.8,
        "timestamp",
        metadata={"runtime": 2},
        created_at="two",
        uuid="two",
    )
    assert evidence_one == evidence_two

    context_one = MarketContext("EURUSD", "M1", "timestamp", metadata={"runtime": 1})
    context_two = MarketContext("EURUSD", "M1", "timestamp", metadata={"runtime": 2})
    assert context_one == context_two


def test_legacy_payloads_without_identity_metadata_remain_readable() -> None:
    candle = Candle.from_dict(
        {
            "timestamp": "2025-01-01T00:00:00Z",
            "symbol": "EURUSD",
            "timeframe": "M1",
            "open": 1.0,
            "high": 1.2,
            "low": 0.9,
            "close": 1.1,
            "volume": 1.0,
        }
    )
    evidence = Evidence.from_dict(
        {
            "id": "evidence",
            "source": "legacy",
            "category": "structure",
            "direction": Direction.BUY.value,
            "confidence": 0.8,
            "timestamp": "timestamp",
        }
    )
    context = MarketContext.from_dict(
        {"symbol": "EURUSD", "timeframe": "M1", "timestamp": "timestamp"}
    )
    decision = Decision.from_dict(
        {
            "id": "decision",
            "decision_type": DecisionType.WAIT.value,
            "reason": "legacy",
        }
    )
    event = BaseEvent.from_dict({"id": "event", "timestamp": "timestamp"})
    price = Price.from_dict(1.0)

    assert all(item.schema_version == 1 for item in (candle, evidence, context, decision, event))
    assert float(price) == 1.0
