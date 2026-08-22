"""Component tests for A05-E05 deterministic temporal dependency validation."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from itertools import permutations
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.evidence.graph import DependencyDiagnostics, DependencyGraph
from epip.governance import GovernanceEpoch
from epip.temporal.availability import AvailabilityDecision
from epip.temporal.completeness import CompletenessOutcome
from epip.temporal.dependency import (
    TemporalDependencyDiagnostics,
    TemporalDependencyValidation,
    TemporalDependencyValidator,
)
from epip.temporal.model import (
    CanonicalInstant,
    CanonicalInterval,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.observation import ObservationValidation
from epip.temporal.timeframe import TemporalMappingContract
from tests.temporal.test_completeness import (
    _availability as _base_availability,
)
from tests.temporal.test_completeness import (
    _instant,
    _interval,
)
from tests.temporal.test_completeness import (
    _observation as _base_observation,
)
from tests.temporal.test_completeness import (
    _outcome as _base_outcome,
)
from tests.temporal.test_timeframe import _mapping as _base_mapping


def _graph(
    nodes: tuple[str, ...] = ("node-source", "node-target"),
    edges: tuple[tuple[str, str], ...] = (("node-source", "node-target"),),
    **changes: object,
) -> DependencyGraph:
    values: dict[str, object] = {
        "snapshot_identity": "snapshot-1",
        "manifest_reference": "manifest-1",
        "governance_epoch": GovernanceEpoch(5),
        "nodes": nodes,
        "edges": edges,
        "selected_candidates": (),
    }
    values.update(changes)
    diagnostics = DependencyDiagnostics(
        cast(str, values["snapshot_identity"]),
        cast(str, values["manifest_reference"]),
        cast(GovernanceEpoch, values["governance_epoch"]),
        (),
        (),
        edges,
        cast(tuple[str, ...], values["nodes"]),
        cast(tuple[tuple[str, str], ...], values["edges"]),
        (),
    )
    return DependencyGraph(
        cast(str, values["snapshot_identity"]),
        cast(str, values["manifest_reference"]),
        cast(GovernanceEpoch, values["governance_epoch"]),
        cast(tuple[str, ...], values["nodes"]),
        cast(tuple[tuple[str, str], ...], values["edges"]),
        (),
        diagnostics,
    )


def _observation(
    identity: str,
    value: CanonicalInstant | CanonicalInterval,
    **changes: object,
) -> ObservationValidation:
    return _base_observation(identity, value, **changes)


def _availability(identity: str, **changes: object) -> AvailabilityDecision:
    return _base_availability(identity, **changes)


def _completeness(
    identity: str,
    interval: CanonicalInterval,
    **changes: object,
) -> CompletenessOutcome:
    values: dict[str, object] = {
        "outcome_identity": f"complete-{identity}",
        "artifact_identities": (identity,),
        "source_temporal_boundaries": (f"boundary-{identity}",),
        "consumer_temporal_boundaries": ("consumer-use-1",),
        "knowledge_boundaries": (_instant(300),),
        "revision_lineages": ((f"publication-{identity}",),),
        "interval_memberships": ((identity, interval),),
        "required_intervals": (interval,),
        "closure_facts": ((identity, "POINT"),),
    }
    values.update(changes)
    return _base_outcome(**values)


def _mapping(**changes: object) -> TemporalMappingContract:
    return _base_mapping(**changes)


def _inputs(
    relationship: str = "HISTORICAL",
    mapping_identity: str | None = None,
    source_value: CanonicalInstant | CanonicalInterval | None = None,
    target_value: CanonicalInstant | CanonicalInterval | None = None,
) -> dict[str, object]:
    source = source_value or _instant(30)
    target = target_value or (_instant(30) if relationship == "SAME_TIME" else _instant(90))
    source_interval = source if isinstance(source, CanonicalInterval) else _interval(30, 31)
    target_interval = (
        target
        if isinstance(target, CanonicalInterval)
        else _interval(target.value, target.value + 1)
    )
    return {
        "graph": _graph(),
        "mappings": (),
        "availability": (_availability("source"), _availability("target")),
        "observations": (
            _observation("source", source),
            _observation("target", target),
        ),
        "completeness": (
            _completeness("source", source_interval),
            _completeness("target", target_interval),
        ),
        "dependency_facts": (
            (
                "dependency-1",
                "node-source",
                "node-target",
                "source",
                "target",
                relationship,
                mapping_identity,
            ),
        ),
        "consumer_requirements": (("dependency-1", True, True, "SOURCE_NOT_AFTER_TARGET"),),
        "compatibility_facts": (("dependency-1", True, "compatibility-1"),),
        "policy_identity": "dependency-policy",
        "policy_version": "1.0.0",
    }


def _validate(**changes: object) -> TemporalDependencyDiagnostics:
    values = _inputs()
    values.update(changes)
    return TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]


def _validation(**changes: object) -> TemporalDependencyValidation:
    original = _validate().validations[0]
    values = {name: getattr(original, name) for name in original._field_names}
    values.update(changes)
    return TemporalDependencyValidation(**values)


def _reason(
    validation: TemporalDependencyValidation, **changes: object
) -> TemporalDiagnosticReason:
    values: dict[str, object] = {
        "code": TemporalDiagnosticCode.INCOMPLETE_WINDOW,
        "affected_evidence": validation.dependency_identity,
        "source_boundary": validation.source_boundary,
        "consumer_boundary": validation.consumer_boundary,
        "timeframe_identity": validation.source_timeframe_identity,
        "calendar_identity": validation.source_calendar_identity,
        "knowledge_boundary": validation.target_knowledge_boundary,
        "revision_lineage": validation.source_revision_lineage,
        "policy_version": validation.policy_version,
        "reason": "dependency context",
    }
    values.update(changes)
    return TemporalDiagnosticReason(**values)  # type: ignore[arg-type]


def test_public_production_inventory_is_exact() -> None:
    from epip.temporal import dependency

    public = {
        name
        for name, value in vars(dependency).items()
        if not name.startswith("_")
        and isinstance(value, type)
        and value.__module__ == dependency.__name__
    }
    assert public == {
        "TemporalDependencyDiagnostics",
        "TemporalDependencyValidation",
        "TemporalDependencyValidator",
    }


@pytest.mark.parametrize("relationship", ["SAME_TIME", "HISTORICAL", "CROSS_TIME"])
def test_same_and_cross_time_dependencies_are_validated(relationship: str) -> None:
    values = _inputs(relationship)
    result = TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    validation = result.validations[0]
    assert validation.relationship == relationship
    assert validation.valid
    assert validation.graph_edges == (("node-source", "node-target"),)
    assert validation.mapping_identity is None


def test_cross_timeframe_mapping_membership_and_compatibility() -> None:
    source = _interval(0, 60)
    target = _interval(0, 3600)
    values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", source, target)
    values["mappings"] = (_mapping(),)
    values["observations"] = (
        _observation("source", source),
        _observation(
            "target",
            target,
            timeframe_identity="H1",
            timeframe_version="1.0.0",
        ),
    )
    result = TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    assert result.validations[0].mapping_identity == "mapping-m1-h1"
    assert result.validations[0].source_interval == source
    assert result.validations[0].target_interval == target


def test_mapping_facts_are_independently_preserved_and_deterministic() -> None:
    source = _interval(0, 60)
    target = _interval(0, 3600)
    values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", source, target)
    mapping = _mapping()
    values["mappings"] = (mapping,)
    values["observations"] = (
        _observation("source", source),
        _observation("target", target, timeframe_identity="H1"),
    )
    first = TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    second = TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    validation = first.validations[0]
    assert dict(validation.mapping_facts) == {
        "alignment_rule": mapping.alignment_rule,
        "closure_requirement": mapping.closure_requirement,
        "completeness_requirement": mapping.completeness_requirement,
        "conflict_rule": mapping.conflict_rule,
        "mapping_identity": mapping.mapping_identity,
        "mapping_version": mapping.mapping_version,
        "membership_rule": mapping.membership_rule,
        "policy_version": mapping.policy_version,
        "revision_propagation_rule": mapping.revision_propagation_rule,
        "source_timeframe_identity": mapping.source_timeframe_identity,
        "source_timeframe_version": mapping.source_timeframe_version,
        "target_timeframe_identity": mapping.target_timeframe_identity,
        "target_timeframe_version": mapping.target_timeframe_version,
        "visibility_rule": mapping.visibility_rule,
    }
    assert validation.mapping_authority == (
        mapping.authority.authority_role,
        mapping.authority.authority_identity,
        mapping.authority.authority_version,
        mapping.authority.governance_epoch,
    )
    assert first == second
    assert hash(first) == hash(second)


def test_permutation_repetition_equality_hashing_and_input_preservation() -> None:
    values = _inputs()
    before = tuple(values.values())
    results = {
        TemporalDependencyValidator.validate(
            cast(DependencyGraph, values["graph"]),
            (),
            tuple(availability),
            tuple(observations),
            tuple(completeness),
            cast(
                tuple[tuple[str, str, str, str, str, str, str | None], ...],
                values["dependency_facts"],
            ),
            cast(tuple[tuple[str, bool, bool, str], ...], values["consumer_requirements"]),
            cast(tuple[tuple[str, bool, str], ...], values["compatibility_facts"]),
            "dependency-policy",
            "1.0.0",
        )
        for availability, observations, completeness in zip(
            permutations(cast(tuple[AvailabilityDecision, ...], values["availability"])),
            permutations(cast(tuple[ObservationValidation, ...], values["observations"])),
            permutations(cast(tuple[CompletenessOutcome, ...], values["completeness"])),
            strict=True,
        )
    }
    assert len(results) == 1
    result = results.pop()
    assert result == _validate()
    assert hash(result) == hash(_validate())
    assert before == tuple(values.values())


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("graph", cast(Any, "graph"), "frozen A04 graph"),
        ("mappings", cast(Any, []), "immutable tuple"),
        ("availability", cast(Any, []), "immutable tuple"),
        ("observations", cast(Any, []), "immutable tuple"),
        ("completeness", cast(Any, []), "immutable tuple"),
        ("dependency_facts", cast(Any, []), "immutable tuple"),
        ("consumer_requirements", cast(Any, []), "immutable tuple"),
        ("compatibility_facts", cast(Any, []), "immutable tuple"),
        ("mappings", cast(Any, ("mapping",)), "unsupported fact"),
        ("availability", cast(Any, ("availability",)), "unsupported fact"),
        ("observations", cast(Any, ("observation",)), "unsupported fact"),
        ("completeness", cast(Any, ("completeness",)), "unsupported fact"),
    ],
)
def test_invalid_input_types_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(**{field: value})


def test_graph_context_and_topology_fail_closed() -> None:
    invalid = _graph(nodes=())
    with pytest.raises(DataIntegrityError, match="incomplete or inconsistent"):
        _validate(graph=invalid)
    with pytest.raises(DataIntegrityError, match="complete A04 topology"):
        _validate(dependency_facts=())
    with pytest.raises(DataIntegrityError, match="endpoint is absent"):
        _validate(graph=_graph(nodes=("node-target",)))


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("dependency_facts", (("short",),), "unsupported fact"),
        (
            "dependency_facts",
            (
                (
                    "dependency-1",
                    "node-source",
                    "node-target",
                    "source",
                    "target",
                    "HISTORICAL",
                    None,
                ),
                (
                    "dependency-1",
                    "node-source",
                    "node-target",
                    "source",
                    "target",
                    "HISTORICAL",
                    None,
                ),
            ),
            "identities must be unique",
        ),
        (
            "consumer_requirements",
            (("dependency-1", "yes", True, "SOURCE_NOT_AFTER_TARGET"),),
            "unsupported fact",
        ),
        (
            "consumer_requirements",
            (("dependency-1", True, True, "UNKNOWN"),),
            "rule is unsupported",
        ),
        ("compatibility_facts", (("dependency-1", "yes", "v1"),), "unsupported fact"),
    ],
)
def test_authoritative_fact_validation(field: str, value: object, message: str) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError), match=message):
        _validate(**{field: value})


def test_missing_and_duplicate_policy_bindings_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="every dependency"):
        _validate(consumer_requirements=())
    duplicate_requirement = (
        ("dependency-1", True, True, "SOURCE_NOT_AFTER_TARGET"),
        ("dependency-1", True, True, "SOURCE_NOT_AFTER_TARGET"),
    )
    with pytest.raises(DataIntegrityError, match="requirement identities"):
        _validate(consumer_requirements=duplicate_requirement)
    duplicate_compatibility = (
        ("dependency-1", True, "v1"),
        ("dependency-1", True, "v1"),
    )
    with pytest.raises(DataIntegrityError, match="compatibility fact identities"):
        _validate(compatibility_facts=duplicate_compatibility)


@pytest.mark.parametrize(
    ("field", "value", "message"),
    [
        ("observations", (), "observation is missing"),
        ("availability", (), "availability is missing"),
        ("completeness", (), "completeness is missing"),
    ],
)
def test_missing_predecessors_fail_closed(field: str, value: object, message: str) -> None:
    with pytest.raises(DataIntegrityError, match=message):
        _validate(**{field: value})


def test_inconsistent_and_ineligible_predecessors_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="context is inconsistent"):
        _validate(
            observations=(
                _observation("source", _instant(30), consumer_temporal_boundary="other"),
                _observation("target", _instant(90)),
            )
        )
    with pytest.raises(DataIntegrityError, match="not temporally eligible"):
        _validate(
            availability=(
                _availability("source", provisionally_temporally_eligible=False),
                _availability("target"),
            )
        )


def test_relationship_conflicts_and_future_dependencies_fail_closed() -> None:
    with pytest.raises(DataIntegrityError, match="same-time dependency"):
        values = _inputs("SAME_TIME", target_value=_instant(90))
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="points into the future"):
        values = _inputs("HISTORICAL", source_value=_instant(90), target_value=_instant(30))
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="not cross-time"):
        values = _inputs("CROSS_TIME", source_value=_instant(30), target_value=_instant(30))
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="relationship is unsupported"):
        _validate(
            dependency_facts=(
                (
                    "dependency-1",
                    "node-source",
                    "node-target",
                    "source",
                    "target",
                    "UNKNOWN",
                    None,
                ),
            )
        )
    with pytest.raises(DataIntegrityError, match="canonical temporal basis"):
        _validate(
            observations=(
                _observation("source", _instant(30, precision="millisecond")),
                _observation("target", _instant(90)),
            )
        )
    with pytest.raises(DataIntegrityError, match="hides conversion"):
        values = _inputs("HISTORICAL")
        observations = list(cast(tuple[ObservationValidation, ...], values["observations"]))
        observations[1] = _observation("target", _instant(90), timeframe_identity="H1")
        values["observations"] = tuple(observations)
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="hides aggregation"):
        values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", _interval(), _interval())
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]


def test_mapping_fail_closed_cases() -> None:
    source, target = _interval(), _interval(0, 3600)
    values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", source, target)
    target_observation = _observation("target", target, timeframe_identity="H1")
    values["observations"] = (_observation("source", source), target_observation)
    with pytest.raises(DataIntegrityError, match="missing or unsupported"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    values["mappings"] = (_mapping(conflict_rule="PREFER_SOURCE"),)
    with pytest.raises(DataIntegrityError, match="rules are unsupported"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    values["mappings"] = (_mapping(),)
    values["observations"] = (
        _observation("source", _interval(60, 120)),
        target_observation,
    )
    with pytest.raises(DataIntegrityError, match="alignment or interval membership"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError, match="unexpected mapping"):
        _validate(
            dependency_facts=(
                (
                    "dependency-1",
                    "node-source",
                    "node-target",
                    "source",
                    "target",
                    "HISTORICAL",
                    "mapping",
                ),
            )
        )


def test_mapping_requirements_cannot_be_weakened_by_consumer_flags() -> None:
    source, target = _interval(), _interval(0, 3600)
    values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", source, target)
    values["mappings"] = (_mapping(),)
    values["consumer_requirements"] = (("dependency-1", False, False, "SOURCE_NOT_AFTER_TARGET"),)
    values["observations"] = (
        _observation("source", source),
        _observation(
            "target",
            target,
            timeframe_identity="H1",
            provisional=True,
            closure_state="OPEN",
        ),
    )
    with pytest.raises(DataIntegrityError, match="requires final target closure"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]
    values["observations"] = (
        _observation("source", source),
        _observation("target", target, timeframe_identity="H1"),
    )
    values["completeness"] = (
        _completeness("source", source),
        _completeness(
            "target",
            target,
            declared_complete=False,
            complete=False,
            provisional=True,
        ),
    )
    with pytest.raises(DataIntegrityError, match="complete target membership"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]


def test_hidden_inheritance_has_dedicated_fail_closed_validation() -> None:
    source, target = _interval(), _interval(0, 3600)
    values = _inputs("CROSS_TIMEFRAME", "mapping-m1-h1", source, target)
    values["mappings"] = (_mapping(revision_propagation_rule="INHERIT_SOURCE_REVISION"),)
    values["observations"] = (
        _observation("source", source),
        _observation("target", target, timeframe_identity="H1"),
    )
    with pytest.raises(DataIntegrityError, match="hidden temporal inheritance"):
        TemporalDependencyValidator.validate(**values)  # type: ignore[arg-type]


def test_closure_completeness_knowledge_and_compatibility_fail_closed() -> None:
    provisional = _observation("source", _instant(30), provisional=True)
    with pytest.raises(DataIntegrityError, match="requires final closure"):
        _validate(observations=(provisional, _observation("target", _instant(90))))
    incomplete = _completeness(
        "source",
        _interval(30, 31),
        declared_complete=False,
        complete=False,
        provisional=True,
    )
    with pytest.raises(DataIntegrityError, match="requires complete windows"):
        _validate(completeness=(incomplete, _completeness("target", _interval(90, 91))))
    with pytest.raises(DataIntegrityError, match="source exceeds"):
        _validate(
            observations=(
                _observation("source", _instant(30), knowledge_boundary=_instant(301)),
                _observation("target", _instant(90)),
            ),
            availability=(
                _availability("source", knowledge_boundary=_instant(301)),
                _availability("target"),
            ),
            completeness=(
                _completeness("source", _interval(30, 31), knowledge_boundaries=(_instant(301),)),
                _completeness("target", _interval(90, 91)),
            ),
        )
    with pytest.raises(DataIntegrityError, match="must be equal"):
        _validate(
            consumer_requirements=(("dependency-1", True, True, "SAME_KNOWLEDGE_BOUNDARY"),),
            observations=(
                _observation("source", _instant(30), knowledge_boundary=_instant(299)),
                _observation("target", _instant(90)),
            ),
            availability=(
                _availability("source", knowledge_boundary=_instant(299)),
                _availability("target"),
            ),
            completeness=(
                _completeness("source", _interval(30, 31), knowledge_boundaries=(_instant(299),)),
                _completeness("target", _interval(90, 91)),
            ),
        )
    with pytest.raises(DataIntegrityError, match="rejects the dependency"):
        _validate(compatibility_facts=(("dependency-1", False, "v1"),))


@pytest.mark.parametrize(
    "changes",
    [
        {"relationship": "UNKNOWN"},
        {"source_revision_lineage": cast(Any, [])},
        {"mapping_identity": "mapping", "mapping_version": None},
        {"mapping_facts": cast(Any, [])},
        {"mapping_facts": (("mapping_identity", "mapping"),)},
        {
            "mapping_identity": "mapping",
            "mapping_version": "1.0.0",
            "mapping_facts": (("mapping_identity", "mapping"),),
            "mapping_authority": cast(Any, ("role", "identity", "version", 5)),
        },
        {
            "mapping_identity": "mapping",
            "mapping_version": "1.0.0",
            "mapping_facts": (("mapping_identity", "mapping"),),
            "mapping_authority": None,
        },
        {"source_interval": cast(Any, "interval")},
        {"source_knowledge_boundary": cast(Any, "instant")},
        {"source_complete": cast(Any, 1)},
        {"valid": False},
        {"governance_epoch": cast(Any, 5)},
        {"graph_nodes": cast(Any, [])},
        {"graph_edges": cast(Any, [])},
        {"consumer_requirement": cast(Any, (True, "yes", "rule"))},
    ],
)
def test_validation_invalid_state_is_rejected(changes: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, MissingFieldError)):
        _validation(**changes)


def test_diagnostics_are_immutable_canonical_and_attributed() -> None:
    validation = _validation()
    diagnostics = TemporalDependencyDiagnostics((validation,))
    assert diagnostics == _validate()
    assert hash(diagnostics) == hash(_validate())
    assert validation != object()
    with pytest.raises(FrozenInstanceError):
        validation.valid = False
    with pytest.raises(FrozenInstanceError):
        diagnostics.reasons = ()
    with pytest.raises(DataIntegrityError, match="duplicate validations"):
        TemporalDependencyDiagnostics((validation, validation))
    with pytest.raises(DataIntegrityError, match="immutable validations"):
        TemporalDependencyDiagnostics(cast(Any, []))
    with pytest.raises(DataIntegrityError, match="immutable reasons"):
        TemporalDependencyDiagnostics((validation,), cast(Any, []))
    reason = TemporalDiagnosticReason(
        TemporalDiagnosticCode.INCOMPLETE_WINDOW,
        "orphan",
        "source",
        "target",
        "M1",
        "calendar-xpar",
        _instant(300),
        (),
        "1.0.0",
        "orphan",
    )
    with pytest.raises(DataIntegrityError, match="orphaned or mismatched"):
        TemporalDependencyDiagnostics((validation,), (reason,))
    attributed = _reason(validation, reason="duplicate")
    assert TemporalDependencyDiagnostics((validation,), (attributed,)).reasons == (attributed,)
    with pytest.raises(DataIntegrityError, match="orphaned or mismatched"):
        TemporalDependencyDiagnostics(
            (validation,),
            (_reason(validation, source_boundary="mismatched"),),
        )
    with pytest.raises(DataIntegrityError, match="duplicate reasons"):
        TemporalDependencyDiagnostics((validation,), (attributed, attributed))
    with pytest.raises(DataIntegrityError, match="duplicate inconsistent bindings"):
        TemporalDependencyDiagnostics(
            (validation,),
            (attributed, _reason(validation, reason="conflicting diagnostic")),
        )


def test_ambiguous_diagnostic_binding_is_rejected() -> None:
    first = _validation()
    second = _validation(compatibility_policy_version="compatibility-2")
    reason = _reason(first)
    with pytest.raises(DataIntegrityError, match="binding is ambiguous"):
        TemporalDependencyDiagnostics((first, second), (reason,))


def test_no_successor_or_forbidden_responsibilities() -> None:
    forbidden = {
        "build_graph",
        "select_provider",
        "aggregate",
        "execute",
        "resolve_revision",
        "determine_usability",
        "replay",
        "certify",
        "close_programme",
        "schedule",
    }
    assert forbidden.isdisjoint(vars(TemporalDependencyValidator))
