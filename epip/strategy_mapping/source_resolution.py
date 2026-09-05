"""Pure structural source resolution for explicitly frame-scoped selectors."""

from __future__ import annotations

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import exact
from epip.strategy_mapping.direction_policy import SourceSelector
from epip.strategy_mapping.mtf_bundle import MultiTimeframeAnalyticalBundle
from epip.strategy_mapping.source_binding import AnalyticalSourceBinding
from epip.strategy_runtime.mtf import TimeframeRole

_ROLE_ORDER = {
    TimeframeRole.PRIMARY: 0,
    TimeframeRole.HIGHER: 1,
    TimeframeRole.LOWER: 2,
}


def resolve_source_bindings(
    selector: SourceSelector,
    bundle: MultiTimeframeAnalyticalBundle,
    *,
    active_role: TimeframeRole | None = None,
) -> tuple[AnalyticalSourceBinding, ...]:
    """Resolve exact structural matches without invoking semantic rules."""
    exact(selector, SourceSelector, "selector")
    exact(bundle, MultiTimeframeAnalyticalBundle, "bundle")
    roles: tuple[TimeframeRole, ...]
    if active_role is not None:
        exact(active_role, TimeframeRole, "active_role")
        if active_role not in selector.frame_roles:
            raise DataIntegrityError("active frame role is not admitted by selector")
        roles = (active_role,)
    else:
        roles = selector.frame_roles

    frames = tuple(
        sorted(
            bundle.frames,
            key=lambda item: (_ROLE_ORDER[item.frame.role], item.frame.timeframe),
        )
    )
    selected: list[AnalyticalSourceBinding] = []
    for role in roles:
        role_frames = tuple(item for item in frames if item.frame.role is role)
        if not role_frames:
            raise DataIntegrityError("selector declares a frame role absent from bundle")
        role_matches: list[AnalyticalSourceBinding] = []
        for frame in role_frames:
            matches = tuple(
                sorted(
                    (
                        source
                        for source in frame.sources
                        if source.source_kind is selector.source_kind
                        and source.source_contract == selector.source_contract
                    ),
                    key=lambda source: source.canonical_key(),
                )
            )
            role_matches.extend(matches)
        if not role_matches:
            return ()
        selected.extend(role_matches)

    identities = tuple(source.source_binding_id for source in selected)
    if len(set(identities)) != len(identities):
        raise DataIntegrityError("resolved source bindings contain duplicate identities")
    return tuple(selected)


__all__ = ["resolve_source_bindings"]
