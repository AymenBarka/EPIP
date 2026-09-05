# mypy: disable-error-code="arg-type,no-untyped-call,no-untyped-def"
from dataclasses import FrozenInstanceError, replace
from enum import Enum

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime.mtf import MultiTimeframeInputSet, TimeframeInput, TimeframeRole
from epip.swing import SwingSequence


class ForeignRole(Enum):
    PRIMARY = "PRIMARY"


def _selector(selector, roles):
    return replace(selector, frame_roles=roles)


def _source(instrument, rule_id, timeframe, object_id, kind=AnalyticalSourceKind.SWING):
    del rule_id
    payload = SwingSequence("EURUSD", timeframe, ())
    return AnalyticalSourceBinding.create(
        source_kind=kind,
        source_contract_version="1",
        source_object_id=object_id,
        instrument=instrument,
        timeframe=timeframe,
        observation_timestamp="2026-01-01T09:00:00Z",
        availability_timestamp="2026-01-01T09:00:01Z",
        as_of_timestamp="2026-01-01T10:00:00Z",
        revision=RevisionIdentity(object_id, f"revision-{object_id}", 0, None),
        superseded_at=None,
        closed=True,
        provenance_ref=object_id,
        payload=payload,
    )


def _frame(role, timeframe, source):
    item = TimeframeInput(
        timeframe,
        role,
        "2026-01-01T08:00:00Z",
        "2026-01-01T09:00:00Z",
        "2026-01-01T10:00:00.000000Z",
        True,
        (source.source_object_id,),
        (source.provenance_ref,),
    )
    return TimeframeAnalyticalFrame.create(item, (source,), (source.provenance_ref,))


def _bundle(rule):
    del rule
    instrument = InstrumentBinding.create("instrument", "EURUSD", (), "1")
    primary_source = _source(instrument, None, "H1", "primary")
    higher_source = _source(instrument, None, "H4", "higher")
    lower_source = _source(instrument, None, "M15", "lower")
    frames = (
        _frame(TimeframeRole.HIGHER, "H4", higher_source),
        _frame(TimeframeRole.LOWER, "M15", lower_source),
        _frame(TimeframeRole.PRIMARY, "H1", primary_source),
    )
    coherence = MultiTimeframeInputSet.create(
        "H1",
        "2026-01-01T10:00:00.000000Z",
        tuple(sorted((frame.frame for frame in frames), key=lambda item: item.timeframe)),
    )
    bundle = MultiTimeframeAnalyticalBundle.create(instrument, coherence, frames, "manifest")
    return bundle, primary_source, higher_source, lower_source


@pytest.mark.parametrize(
    "roles",
    [None, (), [], set(), "PRIMARY", TimeframeRole.PRIMARY, (ForeignRole.PRIMARY,)],
)
def test_frame_roles_are_mandatory_exact_non_empty_tuple(selector, roles):
    with pytest.raises(DataIntegrityError):
        _selector(selector, roles)


@pytest.mark.parametrize("role", list(TimeframeRole))
def test_each_exact_role_is_accepted_and_selector_remains_immutable(selector, role):
    scoped = _selector(selector, (role,))
    assert scoped.frame_roles == (role,)
    with pytest.raises(FrozenInstanceError):
        scoped.frame_roles = (TimeframeRole.PRIMARY,)


def test_roles_are_unique_canonical_and_part_of_equality_hash_and_key(selector):
    with pytest.raises(DataIntegrityError):
        _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.PRIMARY))
    reordered = _selector(selector, (TimeframeRole.HIGHER, TimeframeRole.PRIMARY))
    canonical = _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    primary = _selector(selector, (TimeframeRole.PRIMARY,))
    higher = _selector(selector, (TimeframeRole.HIGHER,))
    assert reordered == canonical
    assert reordered.frame_roles == (TimeframeRole.PRIMARY, TimeframeRole.HIGHER)
    assert primary != higher != canonical
    assert len({primary, higher, canonical}) == 3
    assert canonical.canonical_key()[3] == ("PRIMARY", "HIGHER")


def test_selector_tagged_round_trip_and_reconstruction_fail_closed(selector):
    scoped = _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    payload = to_dict(scoped)
    assert from_json(SourceSelector, to_json(scoped)) == scoped
    assert from_dict(SourceSelector, payload) == scoped
    del payload["fields"]["frame_roles"]
    with pytest.raises(DataIntegrityError):
        from_dict(SourceSelector, payload)


def test_selector_reconstruction_rejects_malformed_foreign_and_duplicate_roles(selector):
    payload = to_dict(selector)
    roles = payload["fields"]["frame_roles"]["$tuple"]
    payload["fields"]["frame_roles"]["$tuple"] = roles * 2
    with pytest.raises(DataIntegrityError):
        from_dict(SourceSelector, payload)
    payload = to_dict(selector)
    payload["fields"]["frame_roles"]["$tuple"][0][
        "$enum"
    ] = "epip.strategy_mapping.direction_policy:DirectionFactName"
    with pytest.raises(DataIntegrityError):
        from_dict(SourceSelector, payload)


def test_profile_round_trip_and_scope_changes_fingerprint(semantic_profile, selector):
    assert from_json(StrategySemanticMappingProfile, to_json(semantic_profile)) == semantic_profile

    def with_scope(roles):
        scoped = _selector(selector, roles)
        directions = tuple(
            replace(item, selector=scoped) for item in semantic_profile.direction_policies
        )
        return StrategySemanticMappingProfile.create(
            semantic_profile_id="semantic",
            semantic_profile_version="1",
            parent_profile=semantic_profile.parent_profile,
            direction_policies=directions,
            mtf_direction_policy=semantic_profile.mtf_direction_policy,
            entry_policy=semantic_profile.entry_policy,
            stop_policy=semantic_profile.stop_policy,
            target_policy=semantic_profile.target_policy,
            confidence_policy=semantic_profile.confidence_policy,
            evidence_taxonomy=semantic_profile.evidence_taxonomy,
            global_conflict_action=semantic_profile.global_conflict_action,
        )

    primary = with_scope((TimeframeRole.PRIMARY,))
    higher = with_scope((TimeframeRole.HIGHER,))
    multi = with_scope((TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    reordered = with_scope((TimeframeRole.HIGHER, TimeframeRole.PRIMARY))
    assert (
        len({primary.identity.fingerprint, higher.identity.fingerprint, multi.identity.fingerprint})
        == 3
    )
    assert multi == reordered


def test_resolution_respects_scope_order_and_mtf_active_narrowing(selector, rule):
    bundle, primary, higher, lower = _bundle(rule)
    assert resolve_source_bindings(_selector(selector, (TimeframeRole.PRIMARY,)), bundle) == (
        primary,
    )
    assert resolve_source_bindings(_selector(selector, (TimeframeRole.HIGHER,)), bundle) == (
        higher,
    )
    multi = _selector(selector, (TimeframeRole.HIGHER, TimeframeRole.PRIMARY))
    assert resolve_source_bindings(multi, bundle) == (primary, higher)
    assert resolve_source_bindings(multi, bundle, active_role=TimeframeRole.HIGHER) == (higher,)
    with pytest.raises(DataIntegrityError):
        resolve_source_bindings(multi, bundle, active_role=TimeframeRole.LOWER)
    assert resolve_source_bindings(_selector(selector, (TimeframeRole.LOWER,)), bundle) == (lower,)


def test_resolution_distinguishes_missing_role_from_present_role_without_match(selector, rule):
    bundle, *_ = _bundle(rule)
    primary_frame = next(item for item in bundle.frames if item.frame.role is TimeframeRole.PRIMARY)
    coherence = MultiTimeframeInputSet.create(
        "H1", "2026-01-01T10:00:00.000000Z", (primary_frame.frame,)
    )
    only_primary = MultiTimeframeAnalyticalBundle.create(
        bundle.instrument, coherence, (primary_frame,), bundle.provenance_manifest_id
    )
    with pytest.raises(DataIntegrityError):
        resolve_source_bindings(_selector(selector, (TimeframeRole.HIGHER,)), only_primary)
    unmatched = replace(selector, source_kind=AnalyticalSourceKind.LIQUIDITY)
    assert resolve_source_bindings(unmatched, bundle) == ()


def test_cross_frame_duplicate_binding_identity_fails_closed(selector, rule):
    bundle, primary, higher, _ = _bundle(rule)
    duplicate = object.__new__(AnalyticalSourceBinding)
    for name in higher.__dataclass_fields__:
        object.__setattr__(
            duplicate,
            name,
            primary.source_binding_id if name == "source_binding_id" else getattr(higher, name),
        )
    higher_frame = next(item for item in bundle.frames if item.frame.role is TimeframeRole.HIGHER)
    corrupted_frame = TimeframeAnalyticalFrame.create(
        higher_frame.frame, (duplicate,), (duplicate.provenance_ref,)
    )
    corrupted_bundle = object.__new__(MultiTimeframeAnalyticalBundle)
    for name in bundle.__dataclass_fields__:
        value = getattr(bundle, name)
        if name == "frames":
            value = tuple(
                corrupted_frame if item.frame.role is TimeframeRole.HIGHER else item
                for item in bundle.frames
            )
        object.__setattr__(corrupted_bundle, name, value)
    multi = _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    with pytest.raises(DataIntegrityError):
        resolve_source_bindings(multi, corrupted_bundle)


def test_all_profile_selector_categories_use_the_same_structural_scope(
    semantic_profile, selector, rule
):
    bundle, primary, higher, _ = _bundle(rule)
    scoped = _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    selectors = (
        replace(semantic_profile.direction_policies[0], selector=scoped).selector,
        replace(semantic_profile.entry_policy, allowed_selectors=(scoped,)).allowed_selectors[0],
        replace(semantic_profile.stop_policy, allowed_selectors=(scoped,)).allowed_selectors[0],
        replace(semantic_profile.target_policy, allowed_selectors=(scoped,)).allowed_selectors[0],
        replace(
            semantic_profile.confidence_policy.inputs[0], source_selector=scoped
        ).source_selector,
        replace(semantic_profile.evidence_taxonomy.keys[0], source_selector=scoped).source_selector,
    )
    assert all(resolve_source_bindings(item, bundle) == (primary, higher) for item in selectors)


def test_scope_adds_no_rule_identity_and_profile_closure_is_unchanged(semantic_profile, selector):
    scoped = _selector(selector, (TimeframeRole.PRIMARY, TimeframeRole.HIGHER))
    assert scoped.selector_rule is selector.selector_rule
    assert not any(isinstance(role, RuleIdentity) for role in scoped.frame_roles)
    assert semantic_profile.direction_policies[0].selector.selector_rule is selector.selector_rule
