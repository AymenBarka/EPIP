# mypy: disable-error-code="no-untyped-def,misc"
from dataclasses import FrozenInstanceError, fields
from inspect import signature

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


def test_closed_execution_vocabularies():
    assert len(SemanticRuleFamily) == 13
    assert len(SemanticInvocationKind) == 13
    assert len(SemanticResultKind) == 12
    assert {x.value for x in SemanticRuleState} == {
        "SUCCESS",
        "NO_MATCH",
        "REJECTED",
        "INVALID_INPUT",
        "FAILED",
    }
    assert len(SemanticRuleDiagnosticCode) == 9


@pytest.mark.parametrize("value", [float("nan"), float("inf"), float("-inf"), -0.0])
def test_semantic_value_rejects_noncanonical_float(value):
    with pytest.raises(DataIntegrityError):
        SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=value)


def test_semantic_value_shapes():
    values = (
        SemanticValue(SemanticValueKind.TEXT, text_value="UP"),
        SemanticValue(SemanticValueKind.BOOLEAN, bool_value=True),
        SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=0.5),
        SemanticValue(SemanticValueKind.PRICE, float_value=1.5),
        SemanticValue(SemanticValueKind.PRICE_RANGE, range_lower=1.0, range_upper=2.0),
    )
    assert len(set(values)) == 5
    with pytest.raises(DataIntegrityError):
        SemanticValue(SemanticValueKind.TEXT, text_value="x", bool_value=True)


def test_candidate_identity_and_immutability(rule):
    value = SemanticValue(SemanticValueKind.PRICE, float_value=1.5)
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
    )
    assert candidate == SemanticCandidate(candidate.candidate_id, "s", "p", "i", "H1", rule, value)
    with pytest.raises(DataIntegrityError):
        SemanticCandidate("0" * 64, "s", "p", "i", "H1", rule, value)
    with pytest.raises(FrozenInstanceError):
        candidate.timeframe = "M1"


def test_candidate_roles_preserve_legacy_and_separate_new_semantics(rule):
    value = SemanticValue(SemanticValueKind.PRICE, float_value=1.5)
    legacy = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
    )
    explicit = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=SemanticCandidateRole.UNSPECIFIED,
    )
    start = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=SemanticCandidateRole.ANCHOR_START,
    )
    end = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=SemanticCandidateRole.ANCHOR_END,
    )
    historical_hash = hash(
        (
            legacy.candidate_id,
            "s",
            "p",
            "i",
            "H1",
            rule,
            value,
        )
    )
    assert legacy.role is SemanticCandidateRole.UNSPECIFIED
    assert legacy == explicit and hash(legacy) == hash(explicit) == historical_hash
    assert len({legacy.candidate_id, start.candidate_id, end.candidate_id}) == 3
    assert len({legacy, start, end}) == 3
    with pytest.raises(DataIntegrityError):
        SemanticCandidate(
            start.candidate_id,
            "s",
            "p",
            "i",
            "H1",
            rule,
            value,
            SemanticCandidateRole.ANCHOR_END,
        )


@pytest.mark.parametrize("invalid", ["", " ", "\t\n", None, 1])
def test_semantic_fact_identity_is_exact_immutable_and_validated(invalid):
    fact = SemanticFactIdentity("example.domain", "signal-state", "1")
    assert (fact.namespace, fact.name, fact.version) == ("example.domain", "signal-state", "1")
    assert tuple(item.name for item in fields(fact)) == ("namespace", "name", "version")
    assert not hasattr(fact, "__dict__")
    assert fact < SemanticFactIdentity("example.domain", "signal-state", "2")
    assert hash(fact) == hash(SemanticFactIdentity("example.domain", "signal-state", "1"))
    with pytest.raises(FrozenInstanceError):
        fact.name = "other"
    for field in ("namespace", "name", "version"):
        values = {"namespace": "example.domain", "name": "state", "version": "1"}
        values[field] = invalid
        with pytest.raises(DataIntegrityError):
            SemanticFactIdentity(**values)


@pytest.mark.parametrize(
    ("role", "historical_id"),
    [
        (
            SemanticCandidateRole.UNSPECIFIED,
            "c8c534722cc3ffe43d5eb0ce4c95d869f48ca3ade54a4c488cbe898f5ea2d3fe",
        ),
        (
            SemanticCandidateRole.QUALIFICATION,
            "a3d16c233d9dafc518a8a54815d29df15dec118f7697b0a12029da6218afb29c",
        ),
        (
            SemanticCandidateRole.ANCHOR_START,
            "da75a8d213530cd3dc2bcccc7bd23e23c4775203d1dcbebbdcc938102bda1953",
        ),
        (
            SemanticCandidateRole.ANCHOR_END,
            "84a6d8102ed0c55260964ac525dac1792e2e6958e0aec7d6692e2eb8fafdb2f1",
        ),
        (
            SemanticCandidateRole.ZONE,
            "66c4b8643f16136748d1c18036f1ad5f2f4c9802136e1213bb067135b72415fe",
        ),
        (
            SemanticCandidateRole.ENTRY,
            "2990cb8ab5ec93ce6d4326076d4f86462841386781442ec2ece241515469968f",
        ),
        (
            SemanticCandidateRole.STOP,
            "0e9c8bdccfb38400d89352ecaf76a2366dbabacdb5fb90caf3dd518e78f9b7b6",
        ),
        (
            SemanticCandidateRole.TARGET,
            "c9af39a48e5f88ebbb86b57ba2831c6998a3539859c8bcf7d7c9193790aa234f",
        ),
    ],
)
def test_candidate_fact_identity_preserves_historical_semantics(rule, role, historical_id):
    # Golden IDs measured from the isolated, unchanged A01 commit.
    value = SemanticValue(SemanticValueKind.TEXT, text_value="SAME")
    legacy = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=role,
    )
    positional = SemanticCandidate(historical_id, "s", "p", "i", "H1", rule, value, role)
    keyword = SemanticCandidate(
        candidate_id=historical_id,
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=role,
    )
    explicit = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        role=role,
        fact_identity=None,
    )
    projection = (historical_id, "s", "p", "i", "H1", rule, value)
    historical_hash = hash(
        projection if role is SemanticCandidateRole.UNSPECIFIED else (*projection, role)
    )
    assert positional == keyword == legacy == explicit
    assert legacy.candidate_id == explicit.candidate_id == historical_id
    assert hash(positional) == hash(legacy) == hash(explicit) == historical_hash
    assert legacy.fact_identity is None
    assert tuple(item.name for item in fields(legacy))[-2:] == ("role", "fact_identity")
    if role is SemanticCandidateRole.UNSPECIFIED:
        assert SemanticCandidate(historical_id, "s", "p", "i", "H1", rule, value) == legacy


def test_candidate_fact_identity_separates_same_valued_facts(rule):
    common = {
        "source_binding_id": "s",
        "provenance_ref": "p",
        "instrument_binding_id": "i",
        "timeframe": "H1",
        "source_rule_identity": rule,
        "value": SemanticValue(SemanticValueKind.TEXT, text_value="SAME"),
    }
    first = SemanticCandidate.create(
        **common, fact_identity=SemanticFactIdentity("example.domain", "first", "1")
    )
    second = SemanticCandidate.create(
        **common, fact_identity=SemanticFactIdentity("example.domain", "second", "1")
    )
    default = SemanticCandidate.create(**common)
    assert first != second
    assert hash(first) != hash(second)
    assert first.candidate_id != second.candidate_id
    assert len({default, first, second}) == 3
    assert len({default.candidate_id, first.candidate_id, second.candidate_id}) == 3
    assert len({hash(default), hash(first), hash(second)}) == 3


def test_candidate_fact_identity_type_and_tampering_fail_closed(rule):
    value = SemanticValue(SemanticValueKind.TEXT, text_value="SAME")
    fact = SemanticFactIdentity("example.domain", "first", "1")
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
        fact_identity=fact,
    )
    with pytest.raises(DataIntegrityError):
        SemanticCandidate.create(
            source_binding_id="s",
            provenance_ref="p",
            instrument_binding_id="i",
            timeframe="H1",
            source_rule_identity=rule,
            value=value,
            fact_identity="first",  # type: ignore[arg-type]
        )
    with pytest.raises(DataIntegrityError):
        SemanticCandidate(
            candidate.candidate_id,
            "s",
            "p",
            "i",
            "H1",
            rule,
            value,
            SemanticCandidateRole.UNSPECIFIED,
            SemanticFactIdentity("example.domain", "second", "1"),
        )


@pytest.mark.parametrize("role", list(SemanticCandidateRole))
def test_every_candidate_role_round_trips(rule, role):
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.BOOLEAN, bool_value=True),
        role=role,
    )
    assert from_json(SemanticCandidate, to_json(candidate)) == candidate


def test_candidate_role_rejects_wrong_type(rule):
    with pytest.raises(DataIntegrityError):
        SemanticCandidate.create(
            source_binding_id="s",
            provenance_ref="p",
            instrument_binding_id="i",
            timeframe="H1",
            source_rule_identity=rule,
            value=SemanticValue(SemanticValueKind.BOOLEAN, bool_value=True),
            role="ANCHOR_START",  # type: ignore[arg-type]
        )


def test_protocol_signature_is_exact():
    assert tuple(signature(ExecutableSemanticRule.invoke).parameters) == ("self", "request")


@pytest.mark.parametrize("state", list(SemanticRuleState)[1:])
def test_non_success_candidate_results_forbid_output(state):
    assert CandidateRuleResult(state, (), None).candidates is None


def test_success_result_invariants(rule):
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.PRICE, float_value=1.0),
    )
    assert CandidateRuleResult(SemanticRuleState.SUCCESS, (), (candidate,)).candidates == (
        candidate,
    )
    with pytest.raises(DataIntegrityError):
        CandidateRuleResult(SemanticRuleState.SUCCESS, (), None)
    with pytest.raises(DataIntegrityError):
        ConfidenceRuleResult(SemanticRuleState.SUCCESS, (), 2.0)
    assert (
        DirectionRuleResult(SemanticRuleState.SUCCESS, (), StrategyDirection.BUY).direction
        is StrategyDirection.BUY
    )
