# mypy: disable-error-code="no-untyped-def,misc"
from dataclasses import FrozenInstanceError
from inspect import signature

import pytest

from epip.a07.foundation import StrategyDirection
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


def test_closed_execution_vocabularies():
    assert len(SemanticRuleFamily) == 13
    assert len(SemanticInvocationKind) == len(SemanticResultKind) == 12
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
