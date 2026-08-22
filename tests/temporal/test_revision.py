"""Component tests for A05-E06 deterministic revision validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision, AvailabilityStatus
from epip.temporal.completeness import CompletenessOutcome
from epip.temporal.dependency import TemporalDependencyValidation
from epip.temporal.model import (
    TemporalAuthorityReference,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation
from epip.temporal.revision import RevisionDiagnostics, RevisionValidation, RevisionValidator
from tests.temporal.test_completeness import (
    _availability,
    _instant,
    _interval,
    _observation,
    _outcome,
)
from tests.temporal.test_dependency import _validation as _dependency


def _authority(role: str, epoch: int = 5) -> TemporalAuthorityReference:
    return TemporalAuthorityReference(role, role, "1.0.0", GovernanceEpoch(epoch))


def _authorities() -> tuple[TemporalAuthorityReference, ...]:
    return (
        _authority("correction_authority"),
        _authority("replacement_authority"),
        _authority("withdrawal_authority"),
        _authority("revision_scope_authority"),
    )


def _complete(
    lineage: tuple[str, ...] = ("publication-source",), **changes: object
) -> CompletenessOutcome:
    values: dict[str, object] = {
        "outcome_identity": "complete-source",
        "artifact_identities": ("source",),
        "source_temporal_boundaries": ("boundary-source",),
        "consumer_temporal_boundaries": ("consumer-use-1",),
        "knowledge_boundaries": (_instant(300),),
        "revision_lineages": (lineage,),
        "interval_memberships": (("source", _interval(30, 31)),),
        "required_intervals": (_interval(30, 31),),
        "closure_facts": (("source", "POINT"),),
    }
    values.update(changes)
    return _outcome(**values)


def _predecessors(
    lineage: tuple[str, ...] = ("publication-source",),
    **availability_changes: object,
) -> tuple[
    tuple[AvailabilityDecision, ...],
    tuple[ObservationValidation, ...],
    tuple[CompletenessOutcome, ...],
    tuple[TemporalDependencyValidation, ...],
]:
    return (
        (_availability("source", revision_lineage=lineage, **availability_changes),),
        (_observation("source", _instant(30), revision_lineage=lineage),),
        (_complete(lineage),),
        (_dependency(),),
    )


def _validate(**changes: object) -> RevisionDiagnostics:
    availability, observations, completeness, dependencies = _predecessors()
    values: dict[str, object] = {
        "validation_identity": "revision-validation-1",
        "artifact_identity": "source",
        "availability": availability,
        "observations": observations,
        "completeness": completeness,
        "dependencies": dependencies,
        "correction_facts": (),
        "replacement_facts": (),
        "withdrawal_facts": (),
        "scope_facts": (
            (
                "GLOBAL",
                ("publication-source", "revision-a", "replacement-b"),
                "revision_scope_authority",
            ),
        ),
        "revision_lineage": ("publication-source",),
        "authorities": _authorities(),
        "historical_boundary": _instant(200),
        "prior_plan_interpretation": (("plan-1", "interpretation-1"),),
        "consumer_requirements": (("consumer-policy", True),),
        "policy_identity": "revision-policy",
        "policy_version": "1.0.0",
    }
    values.update(changes)
    return RevisionValidator.validate(**values)  # type: ignore[arg-type]


def _validation(**changes: object) -> RevisionValidation:
    original = _validate().validations[0]
    values = {name: getattr(original, name) for name in original._field_names}
    values.update(changes)
    return RevisionValidation(**values)


def _reason(validation: RevisionValidation, **changes: object) -> TemporalDiagnosticReason:
    values: dict[str, object] = {
        "code": TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION,
        "affected_evidence": validation.artifact_identity,
        "source_boundary": validation.boundary_identity,
        "consumer_boundary": validation.consumer_boundary,
        "timeframe_identity": "M1",
        "calendar_identity": "calendar-xpar",
        "knowledge_boundary": validation.knowledge_boundary,
        "revision_lineage": validation.revision_lineage,
        "policy_version": validation.policy_version,
        "reason": "revision context",
    }
    values.update(changes)
    return TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import revision

    public = {
        name
        for name, value in vars(revision).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == revision.__name__
    }
    assert public == {"RevisionDiagnostics", "RevisionValidation", "RevisionValidator"}


def test_final_usability_consumes_all_mandatory_predecessors() -> None:
    result = _validate()
    validation = result.validations[0]
    assert validation.status is AvailabilityStatus.USABLE
    assert validation.visible
    assert validation.provisionally_temporally_eligible
    assert validation.complete and validation.dependency_valid and validation.revision_valid
    assert result.reasons == ()


def test_determinism_permutation_hashing_and_input_preservation() -> None:
    availability, observations, completeness, dependencies = _predecessors()
    before = (availability, observations, completeness, dependencies)
    results = {
        _validate(
            authorities=tuple(authorities),
        )
        for authorities in permutations(_authorities())
    }
    assert len(results) == 1
    result = results.pop()
    assert result == _validate()
    assert hash(result) == hash(_validate())
    assert before == (availability, observations, completeness, dependencies)


def test_correction_replacement_and_precedence_are_preserved() -> None:
    lineage = ("publication-source", "revision-a", "replacement-b")
    availability, observations, completeness, dependencies = _predecessors(lineage)
    result = _validate(
        availability=availability,
        observations=observations,
        completeness=completeness,
        dependencies=dependencies,
        revision_lineage=lineage,
        correction_facts=(
            ("publication-source", "revision-a", _instant(200), "correction_authority"),
        ),
        replacement_facts=(
            ("revision-a", "replacement-b", "GLOBAL", 10, _instant(250), "replacement_authority"),
        ),
    )
    validation = result.validations[0]
    assert validation.selected_revision_identity == "replacement-b"
    assert validation.correction_facts[0][1] == "revision-a"
    assert validation.replacement_facts[0][2] == "GLOBAL"
    assert validation.status is AvailabilityStatus.USABLE


def test_authorized_withdrawal_prevents_final_usability() -> None:
    result = _validate(
        withdrawal_facts=(("publication-source", "GLOBAL", _instant(250), "withdrawal_authority"),)
    )
    validation = result.validations[0]
    assert validation.withdrawn
    assert validation.status is AvailabilityStatus.OBSOLETE
    assert result.reasons[0].code is TemporalDiagnosticCode.REVISION_LINEAGE_VIOLATION


def test_unsatisfied_consumer_policy_fails_closed_without_usable() -> None:
    result = _validate(consumer_requirements=(("consumer-policy", False),))
    assert result.validations[0].status is AvailabilityStatus.VISIBLE
    assert result.reasons


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("availability", cast(Any, []), "must be immutable"),
        ("observations", cast(Any, []), "must be immutable"),
        ("completeness", cast(Any, []), "must be immutable"),
        ("dependencies", cast(Any, []), "must be immutable"),
        ("correction_facts", cast(Any, []), "must be immutable"),
        ("replacement_facts", cast(Any, []), "must be immutable"),
        ("withdrawal_facts", cast(Any, []), "must be immutable"),
        ("revision_lineage", cast(Any, []), "must be immutable"),
        ("authorities", cast(Any, []), "must be immutable"),
        ("historical_boundary", cast(Any, "time"), "historical boundary is invalid"),
    ],
)
def test_invalid_top_level_inputs_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(**{field: value})


@pytest.mark.parametrize(
    "field", ["validation_identity", "artifact_identity", "policy_identity", "policy_version"]
)
def test_required_text_is_fail_closed(field: str) -> None:
    with pytest.raises(MissingFieldError):
        _validate(**{field: ""})


def test_missing_or_ambiguous_predecessors_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="availability outcome"):
        _validate(availability=())
    with pytest.raises(DataIntegrityError, match="observation outcome"):
        _validate(observations=())
    with pytest.raises(DataIntegrityError, match="completeness outcome"):
        _validate(completeness=())
    with pytest.raises(DataIntegrityError, match="dependency validation"):
        _validate(dependencies=())


def test_inconsistent_predecessors_and_lineage_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="predecessor context"):
        _validate(
            observations=(_observation("source", _instant(30), consumer_temporal_boundary="other"),)
        )
    with pytest.raises(DataIntegrityError, match="lineage does not match"):
        _validate(revision_lineage=("other",))
    with pytest.raises(MissingFieldError, match="revision lineage"):
        _validate(revision_lineage=())


def test_authority_context_fails_closed() -> None:
    with pytest.raises(MissingFieldError, match="authorities"):
        _validate(authorities=())
    with pytest.raises(DataIntegrityError, match="authority context"):
        _validate(authorities=(_authority("correction_authority", epoch=6),))
    with pytest.raises(DataIntegrityError, match="missing or unauthorized"):
        lineage = ("publication-source", "revision-a")
        availability, observations, completeness, dependencies = _predecessors(lineage)
        _validate(
            availability=availability,
            observations=observations,
            completeness=completeness,
            dependencies=dependencies,
            revision_lineage=lineage,
            correction_facts=(
                ("publication-source", "revision-a", _instant(200), "replacement_authority"),
            ),
        )


def test_correction_validation_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="unsupported fact"):
        _validate(correction_facts=cast(Any, (("short",),)))
    with pytest.raises(DataIntegrityError, match="in-place correction"):
        _validate(
            correction_facts=(
                ("publication-source", "publication-source", _instant(200), "correction_authority"),
            )
        )
    with pytest.raises(DataIntegrityError, match="lineage is inconsistent"):
        _validate(
            correction_facts=(
                ("publication-source", "other", _instant(200), "correction_authority"),
            )
        )
    with pytest.raises(DataIntegrityError, match="not visible"):
        lineage = ("publication-source", "revision-a")
        availability, observations, completeness, dependencies = _predecessors(lineage)
        _validate(
            availability=availability,
            observations=observations,
            completeness=completeness,
            dependencies=dependencies,
            revision_lineage=lineage,
            correction_facts=(
                ("publication-source", "revision-a", _instant(301), "correction_authority"),
            ),
        )


def test_replacement_validation_and_conflict_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="unsupported fact"):
        _validate(replacement_facts=cast(Any, (("short",),)))
    with pytest.raises(DataIntegrityError, match="replacement lineage"):
        _validate(
            replacement_facts=(
                (
                    "publication-source",
                    "publication-source",
                    "GLOBAL",
                    1,
                    _instant(200),
                    "replacement_authority",
                ),
            )
        )
    lineage = ("publication-source", "a", "b")
    availability, observations, completeness, dependencies = _predecessors(lineage)
    with pytest.raises(DataIntegrityError, match="competing revisions"):
        _validate(
            availability=availability,
            observations=observations,
            completeness=completeness,
            dependencies=dependencies,
            revision_lineage=lineage,
            replacement_facts=(
                ("publication-source", "a", "GLOBAL", 1, _instant(200), "replacement_authority"),
                ("publication-source", "b", "GLOBAL", 1, _instant(200), "replacement_authority"),
            ),
        )
    future_lineage = ("publication-source", "replacement")
    availability, observations, completeness, dependencies = _predecessors(future_lineage)
    with pytest.raises(DataIntegrityError, match="replacement is not visible"):
        _validate(
            availability=availability,
            observations=observations,
            completeness=completeness,
            dependencies=dependencies,
            revision_lineage=future_lineage,
            replacement_facts=(
                (
                    "publication-source",
                    "replacement",
                    "GLOBAL",
                    1,
                    _instant(301),
                    "replacement_authority",
                ),
            ),
        )


def test_withdrawal_validation_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="unsupported fact"):
        _validate(withdrawal_facts=cast(Any, (("short",),)))
    with pytest.raises(DataIntegrityError, match="scope is unsupported or inapplicable"):
        _validate(withdrawal_facts=(("other", "GLOBAL", _instant(200), "withdrawal_authority"),))
    with pytest.raises(DataIntegrityError, match="not visible"):
        _validate(
            withdrawal_facts=(
                ("publication-source", "GLOBAL", _instant(301), "withdrawal_authority"),
            )
        )


def test_historical_and_policy_facts_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="historical boundary exceeds"):
        _validate(historical_boundary=_instant(301))
    with pytest.raises(MissingFieldError, match="prior plan"):
        _validate(prior_plan_interpretation=())
    with pytest.raises(DataIntegrityError, match="unsupported fact"):
        _validate(prior_plan_interpretation=cast(Any, (("short",),)))
    with pytest.raises(MissingFieldError, match="consumer requirements"):
        _validate(consumer_requirements=())
    with pytest.raises(DataIntegrityError, match="consumer requirements contain"):
        _validate(consumer_requirements=cast(Any, (("policy", "yes"),)))
    with pytest.raises(DataIntegrityError, match="must be unique"):
        _validate(consumer_requirements=(("policy", True), ("policy", True)))


def test_authoritative_scope_facts_fail_closed() -> None:
    lineage = ("publication-source", "revision-a")
    availability, observations, completeness, dependencies = _predecessors(lineage)
    common = {
        "availability": availability,
        "observations": observations,
        "completeness": completeness,
        "dependencies": dependencies,
        "revision_lineage": lineage,
    }
    replacement = (
        ("publication-source", "revision-a", "UNKNOWN", 1, _instant(200), "replacement_authority"),
    )
    with pytest.raises(DataIntegrityError, match="unsupported or inapplicable"):
        _validate(**common, replacement_facts=replacement)
    with pytest.raises(DataIntegrityError, match="unsupported or inapplicable"):
        _validate(
            withdrawal_facts=(
                ("publication-source", "UNKNOWN", _instant(200), "withdrawal_authority"),
            )
        )
    with pytest.raises(DataIntegrityError, match="unsupported or inapplicable"):
        _validate(
            scope_facts=(("GLOBAL", ("other",), "revision_scope_authority"),),
            withdrawal_facts=(
                ("publication-source", "GLOBAL", _instant(200), "withdrawal_authority"),
            ),
        )
    with pytest.raises(DataIntegrityError, match="scope facts contain"):
        _validate(scope_facts=cast(Any, (("short",),)))


@pytest.mark.parametrize(
    ("field", "fact"),
    [
        (
            "correction_facts",
            (
                (
                    "publication-source",
                    "revision-a",
                    _instant(200, time_scale="TAI"),
                    "correction_authority",
                ),
            ),
        ),
        (
            "replacement_facts",
            (
                (
                    "publication-source",
                    "revision-a",
                    "GLOBAL",
                    1,
                    _instant(200, time_scale="TAI"),
                    "replacement_authority",
                ),
            ),
        ),
        (
            "withdrawal_facts",
            (
                (
                    "publication-source",
                    "GLOBAL",
                    _instant(200, time_scale="TAI"),
                    "withdrawal_authority",
                ),
            ),
        ),
    ],
)
def test_incompatible_canonical_temporal_basis_fails_closed(field: str, fact: object) -> None:
    lineage = ("publication-source", "revision-a")
    availability, observations, completeness, dependencies = _predecessors(lineage)
    with pytest.raises(DataIntegrityError, match="temporal basis is incompatible"):
        _validate(
            availability=availability,
            observations=observations,
            completeness=completeness,
            dependencies=dependencies,
            revision_lineage=lineage,
            **{field: fact},
        )
    with pytest.raises(DataIntegrityError, match="temporal basis is incompatible"):
        _validate(historical_boundary=_instant(200, time_scale="TAI"))


@pytest.mark.parametrize(
    "changes",
    [
        {"scope_facts": cast(Any, (("short",),))},
        {"authority_facts": cast(Any, (("short",),))},
        {"correction_facts": cast(Any, (("short",),))},
        {"replacement_facts": cast(Any, (("short",),))},
        {"withdrawal_facts": cast(Any, (("short",),))},
        {"dependency_identities": ()},
    ],
)
def test_validation_rejects_malformed_preserved_nested_facts(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _validation(**changes)


def test_validation_deeply_rejects_inconsistent_preserved_context() -> None:
    base = _validation()
    epoch = base.governance_epoch
    authorities = base.authority_facts
    scope = (("GLOBAL", ("publication-source", "revision-a"), "revision_scope_authority"),)
    correction = (("publication-source", "revision-a", _instant(200), "correction_authority"),)
    replacement = (
        ("publication-source", "revision-a", "GLOBAL", 1, _instant(200), "replacement_authority"),
    )
    withdrawal = (("publication-source", "GLOBAL", _instant(200), "withdrawal_authority"),)
    cases: tuple[dict[str, object], ...] = (
        {"historical_boundary": _instant(200, time_scale="TAI")},
        {"historical_boundary": _instant(301)},
        {"authority_facts": authorities + (authorities[0],)},
        {
            "authority_facts": tuple((*fact[:3], GovernanceEpoch(6)) for fact in authorities),
        },
        {"scope_facts": scope + scope},
        {"scope_facts": (("GLOBAL", ("publication-source",), "correction_authority"),)},
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "correction_facts": (
                (
                    "publication-source",
                    "revision-a",
                    _instant(200, time_scale="TAI"),
                    "correction_authority",
                ),
            ),
        },
        {
            "correction_facts": (
                ("publication-source", "other", _instant(200), "correction_authority"),
            )
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "correction_facts": (
                (
                    "publication-source",
                    "revision-a",
                    _instant(200),
                    "replacement_authority",
                ),
            ),
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "correction_facts": correction + correction,
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "scope_facts": scope,
            "replacement_facts": (
                (
                    "publication-source",
                    "revision-a",
                    "GLOBAL",
                    1,
                    _instant(200, time_scale="TAI"),
                    "replacement_authority",
                ),
            ),
        },
        {
            "replacement_facts": (
                (
                    "publication-source",
                    "other",
                    "GLOBAL",
                    1,
                    _instant(200),
                    "replacement_authority",
                ),
            )
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "scope_facts": (("GLOBAL", ("revision-a",), "revision_scope_authority"),),
            "replacement_facts": replacement,
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "scope_facts": scope,
            "replacement_facts": (
                (
                    "publication-source",
                    "revision-a",
                    "GLOBAL",
                    1,
                    _instant(200),
                    "correction_authority",
                ),
            ),
        },
        {
            "revision_lineage": ("publication-source", "revision-a"),
            "scope_facts": scope,
            "replacement_facts": replacement + replacement,
        },
        {
            "withdrawal_facts": (
                (
                    "publication-source",
                    "GLOBAL",
                    _instant(200, time_scale="TAI"),
                    "withdrawal_authority",
                ),
            )
        },
        {"withdrawal_facts": (("other", "GLOBAL", _instant(200), "withdrawal_authority"),)},
        {
            "scope_facts": (("GLOBAL", ("other",), "revision_scope_authority"),),
            "withdrawal_facts": withdrawal,
        },
        {
            "withdrawal_facts": (
                ("publication-source", "GLOBAL", _instant(200), "correction_authority"),
            )
        },
        {"withdrawal_facts": withdrawal + withdrawal},
        {"prior_plan_interpretation": ()},
        {"dependency_identities": ("dependency", "dependency")},
        {"selected_revision_identity": "other"},
        {"governance_epoch": cast(Any, "epoch")},
    )
    for index, changes in enumerate(cases):
        try:
            _validation(**changes)
        except (DataIntegrityError, MissingFieldError):
            continue
        raise AssertionError(f"case {index} did not fail closed")
    assert epoch == GovernanceEpoch(5)


def test_scope_and_withdrawal_authority_validation_is_fail_closed() -> None:
    with pytest.raises(MissingFieldError, match="scope facts"):
        _validate(scope_facts=())
    scope = (("GLOBAL", ("publication-source",), "revision_scope_authority"),)
    with pytest.raises(DataIntegrityError, match="scopes must be unique"):
        _validate(scope_facts=scope + scope)
    with pytest.raises(DataIntegrityError, match="scope is inconsistent"):
        _validate(
            scope_facts=(("GLOBAL", ("other",), "revision_scope_authority"),),
            withdrawal_facts=(("other", "GLOBAL", _instant(200), "withdrawal_authority"),),
        )


@pytest.mark.parametrize(
    "changes",
    [
        {"publication_time": cast(Any, "time")},
        {"revision_lineage": ()},
        {"correction_facts": cast(Any, [])},
        {"governance_epoch": cast(Any, 5)},
        {"visible": cast(Any, 1)},
        {"status": cast(Any, "USABLE")},
        {"status": AvailabilityStatus.VISIBLE},
    ],
)
def test_validation_invalid_state_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _validation(**changes)


def test_diagnostics_are_immutable_attributed_and_fail_closed() -> None:
    validation = _validation()
    diagnostics = RevisionDiagnostics((validation,))
    assert diagnostics == _validate()
    assert hash(diagnostics) == hash(_validate())
    assert validation != object()
    with pytest.raises(FrozenInstanceError):
        validation.status = AvailabilityStatus.VISIBLE
    with pytest.raises(FrozenInstanceError):
        diagnostics.reasons = ()
    with pytest.raises(DataIntegrityError, match="duplicate validations"):
        RevisionDiagnostics((validation, validation))
    with pytest.raises(DataIntegrityError, match="immutable validations"):
        RevisionDiagnostics(cast(Any, []))
    with pytest.raises(DataIntegrityError, match="immutable reasons"):
        RevisionDiagnostics((validation,), cast(Any, []))
    with pytest.raises(DataIntegrityError, match="orphaned"):
        RevisionDiagnostics((validation,), (_reason(validation, affected_evidence="orphan"),))
    reason = _reason(validation)
    with pytest.raises(DataIntegrityError, match="duplicate reasons"):
        RevisionDiagnostics((validation,), (reason, reason))
    inconsistent = _reason(validation, reason="inconsistent revision context")
    with pytest.raises(DataIntegrityError, match="inconsistent bindings"):
        RevisionDiagnostics((validation,), (reason, inconsistent))
    with pytest.raises(DataIntegrityError, match="orphaned"):
        RevisionDiagnostics((validation,), (_reason(validation, timeframe_identity="other"),))


def test_no_e07_to_e09_or_forbidden_responsibilities() -> None:
    forbidden = {
        "replay",
        "certify",
        "integrated_close",
        "execute",
        "build_graph",
        "manage_lifecycle",
        "mutate_history",
    }
    assert forbidden.isdisjoint(vars(RevisionValidator))


@pytest.mark.parametrize(
    ("field", "fact"),
    [
        ("correction_facts", (("", "revision-a", _instant(200), "correction_authority"),)),
        (
            "replacement_facts",
            (("publication-source", "revision-a", "", 1, _instant(200), "replacement_authority"),),
        ),
        (
            "withdrawal_facts",
            (("publication-source", "", _instant(200), "withdrawal_authority"),),
        ),
    ],
)
def test_revision_nested_scope_and_identity_facts_are_self_contained(
    field: str, fact: object
) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _validation(**{field: fact})


def test_temporal_basis_authority_is_part_of_canonical_validation() -> None:
    with pytest.raises(DataIntegrityError, match="temporal basis is incompatible"):
        _validate(historical_boundary=_instant(200, authority_identity="other-authority"))
