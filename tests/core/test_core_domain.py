from __future__ import annotations

import copy
from dataclasses import FrozenInstanceError

import pytest

from epip.core.candle import Candle
from epip.core.context import MarketContext
from epip.core.decision import Decision
from epip.core.events import (
    BaseEvent,
    DecisionCreated,
    DecisionRejected,
    EvidenceCreated,
    EvidenceRejected,
    ScenarioCreated,
    ScenarioRejected,
)
from epip.core.evidence import Evidence
from epip.core.hypothesis import Hypothesis
from epip.core.scenario import Scenario
from epip.core.types import DecisionType, Direction, ScenarioType
from epip.core.value_objects import Confidence, Price, Probability, RiskScore


def test_candle_validators_and_properties() -> None:
    candle = Candle(
        timestamp="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.1000,
        high=1.1100,
        low=1.0900,
        close=1.1050,
        volume=100.0,
    )

    assert candle.body_size() == pytest.approx(0.0050)
    assert candle.range() == pytest.approx(0.0200)
    assert candle.bullish is True
    assert candle.bearish is False
    assert candle.is_doji() is False
    assert candle.mid_price() == pytest.approx(1.1000)
    assert candle.typical_price() == pytest.approx(1.1017, rel=1e-4)
    assert candle.weighted_price() == pytest.approx(1.1025, rel=1e-4)


def test_candle_rejects_invalid_values() -> None:
    with pytest.raises(ValueError):
        Candle(
            timestamp="2024-01-01T00:00:00Z",
            symbol="EURUSD",
            timeframe="M1",
            open=1.1000,
            high=1.0900,
            low=1.1000,
            close=1.1050,
            volume=10.0,
        )

    with pytest.raises(ValueError):
        Candle(
            timestamp="2024-01-01T00:00:00Z",
            symbol="EURUSD",
            timeframe="M1",
            open=1.1000,
            high=1.1100,
            low=1.0900,
            close=1.1200,
            volume=-1.0,
        )


def test_evidence_is_immutable_and_validated() -> None:
    evidence = Evidence(
        id="ev-1",
        source="plugin-test",
        category="structure",
        direction=Direction.BUY,
        confidence=0.88,
        timestamp="2024-01-01T00:00:00Z",
        metadata={"foo": "bar"},
    )

    assert evidence.confidence == 0.88
    assert evidence.direction == Direction.BUY

    with pytest.raises(ValueError):
        Evidence(
            id="ev-2",
            source="plugin-test",
            category="structure",
            direction=Direction.SELL,
            confidence=1.2,
            timestamp="2024-01-01T00:00:00Z",
            metadata={},
        )

    with pytest.raises(TypeError):
        evidence.metadata["foo"] = "baz"  # type: ignore[index]


def test_scenario_averages_evidence_score() -> None:
    evidence_a = Evidence(
        id="a",
        source="plugin-a",
        category="structure",
        direction=Direction.BUY,
        confidence=0.8,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
    )
    evidence_b = Evidence(
        id="b",
        source="plugin-b",
        category="structure",
        direction=Direction.BUY,
        confidence=0.6,
        timestamp="2024-01-01T00:00:00Z",
        metadata={},
    )

    scenario = Scenario(
        id="sc-1",
        direction=Direction.BUY,
        scenario_type=ScenarioType.CONTINUATION,
        evidence=[evidence_a, evidence_b],
        probability=0.7,
        timestamp="2024-01-01T00:00:00Z",
    )

    assert scenario.global_score == pytest.approx(0.7)
    assert scenario.probability == 0.7
    assert len(scenario.evidence) == 2
    assert scenario.evidence[0].id == "a"


def test_hypothesis_and_decision_are_immutable() -> None:
    scenario = Scenario(
        id="sc-2",
        direction=Direction.BUY,
        scenario_type=ScenarioType.REVERSAL,
        evidence=[],
        probability=0.65,
        timestamp="2024-01-01T00:00:00Z",
    )
    hypothesis = Hypothesis(id="hp-1", scenario=scenario, timestamp="2024-01-01T00:00:00Z")
    decision = Decision(
        id="dec-1",
        decision_type=DecisionType.BUY,
        reason="trend confirmation",
        probability=0.78,
        risk_score=0.2,
        timestamp="2024-01-01T00:00:00Z",
    )

    assert hypothesis.scenario == scenario
    assert decision.decision_type == DecisionType.BUY

    with pytest.raises(FrozenInstanceError):
        hypothesis.scenario = scenario  # type: ignore[misc]


def test_market_context_is_read_only() -> None:
    candle = Candle(
        timestamp="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.0,
        high=1.1,
        low=0.9,
        close=1.05,
        volume=5.0,
    )
    context = MarketContext(
        symbol="EURUSD",
        timeframe="M1",
        timestamp="2024-01-01T00:00:00Z",
        candles=(candle,),
        metadata={"source": "unit-test"},
        plugin_cache={"p": "v"},
    )

    assert context.symbol == "EURUSD"
    assert context.candles[0].symbol == "EURUSD"
    assert context.metadata["source"] == "unit-test"
    assert context.to_dict()["candles"][0]["symbol"] == "EURUSD"
    restored_context = MarketContext.from_dict(context.to_dict())
    assert restored_context.to_json() == context.to_json()
    assert MarketContext.from_json(context.to_json()).to_json() == context.to_json()

    with pytest.raises(FrozenInstanceError):
        context.symbol = "USDJPY"  # type: ignore[misc]


def test_domain_events_are_simple_value_objects() -> None:
    event = BaseEvent(id="evt-1", timestamp="2024-01-01T00:00:00Z")
    evidence_event = EvidenceCreated(
        id="evt-2", timestamp="2024-01-01T00:00:00Z", evidence_id="ev-1"
    )
    scenario_event = ScenarioCreated(
        id="evt-3", timestamp="2024-01-01T00:00:00Z", scenario_id="sc-1"
    )
    decision_event = DecisionCreated(
        id="evt-4", timestamp="2024-01-01T00:00:00Z", decision_id="dec-1"
    )
    rejected_evidence = EvidenceRejected(
        id="evt-5", timestamp="2024-01-01T00:00:00Z", evidence_id="ev-2", reason="low quality"
    )
    rejected_scenario = ScenarioRejected(
        id="evt-6", timestamp="2024-01-01T00:00:00Z", scenario_id="sc-2", reason="unsupported"
    )
    rejected_decision = DecisionRejected(
        id="evt-7", timestamp="2024-01-01T00:00:00Z", decision_id="dec-2", reason="risk exceeded"
    )

    assert isinstance(event, BaseEvent)
    assert evidence_event.evidence_id == "ev-1"
    assert scenario_event.scenario_id == "sc-1"
    assert decision_event.decision_id == "dec-1"
    assert rejected_evidence.reason == "low quality"
    assert rejected_scenario.reason == "unsupported"
    assert rejected_decision.reason == "risk exceeded"


def test_value_objects_and_serialization() -> None:
    confidence = Confidence(0.82)
    probability = Probability(0.61)
    risk_score = RiskScore(0.19)
    price = Price(1.2345)

    for value_object in (confidence, probability, risk_score, price):
        payload = value_object.to_json()
        restored = type(value_object).from_json(payload)
        assert restored == value_object
        assert type(value_object).from_dict(value_object.to_dict()) == value_object

    assert confidence.to_dict()["value"] == 0.82
    assert Probability.from_dict(0.61) == probability
    assert RiskScore.from_dict(0.19) == risk_score
    assert Price.from_dict(1.2345) == price
    with pytest.raises(ValueError):
        Confidence(1.2)


def test_candle_exposes_additional_analytics_and_serialization() -> None:
    previous = Candle(
        timestamp="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.20,
        high=1.25,
        low=1.00,
        close=1.10,
        volume=10.0,
    )
    current = Candle(
        timestamp="2024-01-02T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.09,
        high=1.30,
        low=0.95,
        close=1.21,
        volume=15.0,
    )

    assert current.body() == (1.09, 1.21)
    assert current.upper_wick() == pytest.approx(0.09)
    assert current.lower_wick() == pytest.approx(0.14)
    assert current.is_inside_bar(previous) is False
    assert current.is_outside_bar(previous) is True
    assert current.is_engulfing(previous) is True
    assert current.spread() == pytest.approx(0.35)
    assert current.strength() == pytest.approx(0.3428571429, rel=1e-9)
    assert current.bullish is True
    assert current.bearish is False
    assert current.is_doji() is False
    assert current.mid_price() == pytest.approx(1.125)
    assert current.typical_price() == pytest.approx(1.1533333333, rel=1e-9)
    assert current.weighted_price() == pytest.approx(1.1675, rel=1e-9)

    payload = current.to_dict()
    restored = Candle.from_dict(payload)
    assert restored.to_json() == current.to_json()
    assert restored.to_dict() == payload


def test_evidence_hypothesis_and_events_support_round_trips() -> None:
    evidence = Evidence(
        id="ev-3",
        source="plugin-roundtrip",
        category="structure",
        direction=Direction.BUY,
        confidence=0.74,
        timestamp="2024-01-01T00:00:00Z",
        metadata={"origin": "tests"},
    )
    scenario = Scenario(
        id="sc-3",
        direction=Direction.BUY,
        scenario_type=ScenarioType.CONTINUATION,
        evidence=[evidence],
        probability=0.8,
        timestamp="2024-01-01T00:00:00Z",
    )
    hypothesis = Hypothesis(id="hp-3", scenario=scenario, timestamp="2024-01-01T00:00:00Z")
    event = EvidenceCreated(id="evt-8", timestamp="2024-01-01T00:00:00Z", evidence_id="ev-3")

    assert evidence.to_dict()["confidence"] == 0.74
    assert Evidence.from_dict(evidence.to_dict()).to_json() == evidence.to_json()
    assert Scenario.from_json(scenario.to_json()).to_json() == scenario.to_json()
    assert hypothesis.to_dict()["scenario"]["id"] == "sc-3"
    assert Hypothesis.from_json(hypothesis.to_json()).to_json() == hypothesis.to_json()
    assert event.to_dict()["evidence_id"] == "ev-3"
    assert type(event).from_json(event.to_json()).to_json() == event.to_json()

    for event_instance in (
        EvidenceCreated(id="evt-9", timestamp="2024-01-01T00:00:00Z", evidence_id="ev-4"),
        ScenarioCreated(id="evt-10", timestamp="2024-01-01T00:00:00Z", scenario_id="sc-4"),
        DecisionCreated(id="evt-11", timestamp="2024-01-01T00:00:00Z", decision_id="dec-4"),
        EvidenceRejected(
            id="evt-12",
            timestamp="2024-01-01T00:00:00Z",
            evidence_id="ev-5",
            reason="insufficient confidence",
        ),
        ScenarioRejected(
            id="evt-13",
            timestamp="2024-01-01T00:00:00Z",
            scenario_id="sc-5",
            reason="conflict",
        ),
        DecisionRejected(
            id="evt-14",
            timestamp="2024-01-01T00:00:00Z",
            decision_id="dec-5",
            reason="risk",
        ),
    ):
        payload = event_instance.to_dict()
        restored = type(event_instance).from_dict(payload)
        assert restored.to_dict() == payload
        assert (
            type(event_instance).from_json(event_instance.to_json()).to_json()
            == event_instance.to_json()
        )


def test_domain_models_support_equality_hash_and_deepcopy() -> None:
    candle = Candle(
        timestamp="2024-01-01T00:00:00Z",
        symbol="EURUSD",
        timeframe="M1",
        open=1.0,
        high=1.1,
        low=0.9,
        close=1.05,
        volume=5.0,
    )
    copied = copy.deepcopy(candle)

    assert candle == copied
    assert hash(candle) == hash(copied)
    assert candle.to_dict() == Candle.from_dict(candle.to_dict()).to_dict()

    decision = Decision(
        id="dec-3",
        decision_type=DecisionType.BUY,
        reason="signal",
        probability=0.9,
        risk_score=0.1,
        timestamp="2024-01-01T00:00:00Z",
    )
    decision_copy = copy.deepcopy(decision)
    assert decision == decision_copy
    assert decision.to_json() == Decision.from_json(decision.to_json()).to_json()
