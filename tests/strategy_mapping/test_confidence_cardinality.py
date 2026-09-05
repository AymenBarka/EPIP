# mypy: disable-error-code="no-untyped-def"
from __future__ import annotations

from dataclasses import replace

import pytest

from epip.strategy_mapping._confidence_cardinality import (
    _reduce_confidence_input,
    _reduce_confidence_policy,
)
from epip.strategy_mapping.confidence_policy import (
    ConfidenceInput,
    ConfidenceModelKind,
    ConfidencePolicy,
)
from epip.strategy_mapping.direction_policy import NonAcceptanceAction
from epip.strategy_mapping.rule_execution import (
    SemanticRuleDiagnosticCode,
    SemanticRuleState,
    SemanticValueKind,
)
from epip.strategy_mapping.rule_identity import RuleIdentity
from epip.strategy_mapping.rule_results import CandidateRuleResult
from epip.strategy_mapping.rule_values import SemanticCandidate, SemanticValue
from epip.strategy_runtime.protocols import FactAdapterState


def _candidate(name: str, rule: RuleIdentity) -> SemanticCandidate:
    return SemanticCandidate.create(
        source_binding_id=f"binding-{name}",
        provenance_ref=f"provenance-{name}",
        instrument_binding_id="instrument",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.FINITE_FLOAT, float_value=0.5),
    )


def _policy(
    semantic_profile,
    *,
    kind: ConfidenceModelKind = ConfidenceModelKind.DIRECT,
    inputs: tuple[ConfidenceInput, ...] | None = None,
    missing: NonAcceptanceAction = NonAcceptanceAction.REJECT,
    conflict: NonAcceptanceAction = NonAcceptanceAction.REQUIRE_SINGLE,
) -> ConfidencePolicy:
    base = semantic_profile.confidence_policy
    return ConfidencePolicy(
        base.policy_identity,
        kind,
        base.model_identity,
        base.inputs if inputs is None else inputs,
        base.parameters,
        base.model_identity if kind is ConfidenceModelKind.CALIBRATED else None,
        0.0,
        1.0,
        missing,
        conflict,
    )


def _result(state: SemanticRuleState, candidates=None):
    return CandidateRuleResult(state, (), candidates)


@pytest.mark.parametrize("state", [SemanticRuleState.SUCCESS, SemanticRuleState.NO_MATCH])
def test_zero_and_no_match_use_missing_action_and_preserve_state(semantic_profile, state):
    policy = _policy(semantic_profile, missing=NonAcceptanceAction.NO_FACT)
    item = replace(policy.inputs[0], required=False)
    policy = _policy(semantic_profile, inputs=(item,), missing=NonAcceptanceAction.NO_FACT)
    result = _result(state, () if state is SemanticRuleState.SUCCESS else None)
    outcome = _reduce_confidence_input(item, policy, result)
    assert outcome.omitted and outcome.terminal_state is None
    assert outcome.source_state is state
    assert outcome.diagnostics[0].message == "CONFIDENCE_INPUT_OMITTED"


def test_exactly_one_candidate_is_preserved_without_reconstruction(semantic_profile, rule):
    policy = _policy(semantic_profile)
    candidate = _candidate("x", rule)
    outcome = _reduce_confidence_input(
        policy.inputs[0], policy, _result(SemanticRuleState.SUCCESS, (candidate,))
    )
    assert outcome.value is not None
    assert outcome.value.candidate is candidate
    assert outcome.value.candidate.candidate_id == candidate.candidate_id
    assert outcome.value.candidate.provenance_ref == "provenance-x"
    assert outcome.value.candidate.timeframe == "H1"
    assert outcome.value.candidate.source_rule_identity is rule
    assert outcome.value.candidate.value.kind is SemanticValueKind.FINITE_FLOAT


@pytest.mark.parametrize("count", [2, 5])
def test_multiple_candidates_activate_conflict_without_selecting(semantic_profile, rule, count):
    policy = _policy(
        semantic_profile,
        conflict=NonAcceptanceAction.NO_FACT,
        inputs=(replace(semantic_profile.confidence_policy.inputs[0], required=False),),
    )
    candidates = tuple(_candidate(name, rule) for name in ("z", "a", "m", "b", "q")[:count])
    outcome = _reduce_confidence_input(
        policy.inputs[0], policy, _result(SemanticRuleState.SUCCESS, candidates)
    )
    assert outcome.value is None and outcome.omitted
    assert all(outcome.value is not candidate for candidate in candidates)
    assert outcome.diagnostics[0].message == "CONFIDENCE_INPUT_CONFLICT_OMITTED"


@pytest.mark.parametrize(
    ("required", "action", "terminal", "omitted"),
    [
        (False, NonAcceptanceAction.NO_FACT, None, True),
        (True, NonAcceptanceAction.NO_FACT, FactAdapterState.REJECTED, False),
        (False, NonAcceptanceAction.REJECT, FactAdapterState.REJECTED, False),
        (False, NonAcceptanceAction.REQUIRE_SINGLE, FactAdapterState.REJECTED, False),
        (
            False,
            NonAcceptanceAction.REQUIRE_EXPLICIT_SELECTION_RULE,
            FactAdapterState.INVALID_INPUT,
            False,
        ),
    ],
)
def test_every_action_has_frozen_missing_behavior(
    semantic_profile, required, action, terminal, omitted
):
    item = replace(semantic_profile.confidence_policy.inputs[0], required=required)
    policy = _policy(semantic_profile, inputs=(item,), missing=action)
    outcome = _reduce_confidence_input(item, policy, _result(SemanticRuleState.SUCCESS, ()))
    assert (outcome.terminal_state, outcome.omitted) == (terminal, omitted)


@pytest.mark.parametrize(
    ("required", "action", "terminal", "omitted"),
    [
        (False, NonAcceptanceAction.NO_FACT, None, True),
        (True, NonAcceptanceAction.NO_FACT, FactAdapterState.REJECTED, False),
        (False, NonAcceptanceAction.REJECT, FactAdapterState.REJECTED, False),
        (False, NonAcceptanceAction.REQUIRE_SINGLE, FactAdapterState.REJECTED, False),
        (
            False,
            NonAcceptanceAction.REQUIRE_EXPLICIT_SELECTION_RULE,
            FactAdapterState.INVALID_INPUT,
            False,
        ),
    ],
)
def test_every_action_has_frozen_conflict_behavior(
    semantic_profile, rule, required, action, terminal, omitted
):
    item = replace(semantic_profile.confidence_policy.inputs[0], required=required)
    policy = _policy(semantic_profile, inputs=(item,), conflict=action)
    candidates = (_candidate("z", rule), _candidate("a", rule))
    outcome = _reduce_confidence_input(item, policy, _result(SemanticRuleState.SUCCESS, candidates))
    assert (outcome.terminal_state, outcome.omitted) == (terminal, omitted)


@pytest.mark.parametrize(
    ("state", "adapter_state"),
    [
        (SemanticRuleState.REJECTED, FactAdapterState.REJECTED),
        (SemanticRuleState.INVALID_INPUT, FactAdapterState.INVALID_INPUT),
        (SemanticRuleState.FAILED, FactAdapterState.FAILED),
    ],
)
def test_terminal_rule_states_cannot_be_overridden_by_no_fact(
    semantic_profile, state, adapter_state
):
    item = replace(semantic_profile.confidence_policy.inputs[0], required=False)
    policy = _policy(
        semantic_profile,
        inputs=(item,),
        missing=NonAcceptanceAction.NO_FACT,
        conflict=NonAcceptanceAction.NO_FACT,
    )
    result = CandidateRuleResult(state, (SemanticRuleDiagnosticCode.RULE_REJECTED,), None)
    outcome = _reduce_confidence_input(item, policy, result)
    assert outcome.terminal_state is adapter_state and not outcome.omitted


@pytest.mark.parametrize(
    "kind",
    [
        ConfidenceModelKind.DIRECT,
        ConfidenceModelKind.WEIGHTED,
        ConfidenceModelKind.RULE,
        ConfidenceModelKind.CALIBRATED,
    ],
)
def test_every_variant_rejects_an_empty_runtime_input_set(semantic_profile, kind):
    item = replace(semantic_profile.confidence_policy.inputs[0], required=False)
    policy = _policy(
        semantic_profile,
        kind=kind,
        inputs=(item,),
        missing=NonAcceptanceAction.NO_FACT,
    )
    outcome = _reduce_confidence_policy(policy, ((item, _result(SemanticRuleState.SUCCESS, ())),))
    assert outcome.terminal_state is FactAdapterState.REJECTED
    assert outcome.diagnostics[-1].message == "CONFIDENCE_INPUT_SET_EMPTY"


def test_policy_collection_preserves_order_and_optional_omission(semantic_profile, rule):
    selector = semantic_profile.confidence_policy.inputs[0].source_selector
    inputs = tuple(
        ConfidenceInput(key, selector, required)
        for key, required in (("zeta", False), ("alpha", True), ("beta", False))
    )
    policy = _policy(
        semantic_profile,
        kind=ConfidenceModelKind.WEIGHTED,
        inputs=inputs,
        missing=NonAcceptanceAction.NO_FACT,
    )
    alpha, beta, zeta = policy.inputs
    outcome = _reduce_confidence_policy(
        policy,
        (
            (alpha, _result(SemanticRuleState.SUCCESS, (_candidate("alpha", rule),))),
            (beta, _result(SemanticRuleState.SUCCESS, ())),
            (zeta, _result(SemanticRuleState.SUCCESS, (_candidate("zeta", rule),))),
        ),
    )
    assert tuple(item.input_key for item in outcome.included) == ("alpha", "zeta")
    assert outcome.omitted_input_keys == ("beta",)
    assert outcome.terminal_state is None


def test_policy_collection_fails_fast_at_first_terminal_input(semantic_profile, rule, monkeypatch):
    selector = semantic_profile.confidence_policy.inputs[0].source_selector
    inputs = tuple(ConfidenceInput(key, selector, True) for key in ("alpha", "beta", "zeta"))
    policy = _policy(semantic_profile, kind=ConfidenceModelKind.RULE, inputs=inputs)
    valid = _result(SemanticRuleState.SUCCESS, (_candidate("valid", rule),))
    conflict = _result(SemanticRuleState.SUCCESS, (_candidate("z", rule), _candidate("a", rule)))
    import epip.strategy_mapping._confidence_cardinality as module

    seen = []
    original = module._reduce_confidence_input

    def recording(item, current_policy, result):
        seen.append(item.input_key)
        return original(item, current_policy, result)

    monkeypatch.setattr(module, "_reduce_confidence_input", recording)
    outcome = module._reduce_confidence_policy(
        policy, tuple(zip(policy.inputs, (valid, conflict, valid), strict=True))
    )
    assert seen == ["alpha", "beta"]
    assert outcome.processed_count == 2


def test_reduction_is_deterministic_and_rejects_malformed_result(semantic_profile):
    policy = _policy(semantic_profile)
    item = policy.inputs[0]
    first = _reduce_confidence_input(item, policy, object())
    second = _reduce_confidence_input(item, policy, object())
    assert first == second
    assert first.terminal_state is FactAdapterState.INVALID_INPUT
