"""Tests for read-only deterministic security audit observability."""

from collections.abc import Callable
from dataclasses import FrozenInstanceError

import pytest

from epip.core.security_audit import (
    SECURITY_AUDIT_REGISTRY,
    SecurityAuditEntry,
    SecurityAuditHistory,
    SecurityAuditManager,
    SecurityAuditRegistry,
    SecurityCoverage,
    SecurityHealth,
    SecurityMetric,
    SecurityObservation,
    SecurityObservationKind,
    declared_security_audits,
    get_security_audit,
)


def _observations() -> tuple[SecurityObservation, ...]:
    return (
        SecurityObservation(
            2,
            "observation-2",
            "provider",
            SecurityObservationKind.INCIDENT,
            "critical",
            adopted=True,
        ),
        SecurityObservation(
            1,
            "observation-1",
            "runtime",
            SecurityObservationKind.DECISION,
            "allow",
            policy="disabled",
            adopted=True,
            runtime_active=True,
        ),
    )


def test_official_registry_is_complete_ordered_and_resolvable() -> None:
    entries = declared_security_audits()
    assert entries == tuple(sorted(entries, key=lambda item: item.name))
    assert len(entries) == 6
    assert get_security_audit("runtime-security") is SECURITY_AUDIT_REGISTRY["runtime-security"]


def test_aware_component_resolution_is_additive() -> None:
    entry = SecurityAuditEntry("application", runtime_policy="disabled")

    class Aware:
        @property
        def security_audit_entry(self) -> SecurityAuditEntry:
            return entry

    assert get_security_audit(Aware()) is entry
    with pytest.raises(LookupError):
        get_security_audit("missing")


def test_snapshot_and_history_are_immutable_and_deterministic() -> None:
    manager = SecurityAuditManager(SECURITY_AUDIT_REGISTRY)
    snapshot = manager.snapshot(9, reversed(_observations()))
    assert tuple(item.observation_id for item in snapshot.observations) == (
        "observation-1",
        "observation-2",
    )
    assert snapshot.coverage == SecurityCoverage(10_000, 5_000, 5_000)
    history = SecurityAuditHistory().append(snapshot)
    assert history.snapshots == (snapshot,)
    with pytest.raises(FrozenInstanceError):
        snapshot.logical_time = 10  # type: ignore[misc]


def test_report_is_canonical_and_contains_required_metrics() -> None:
    manager = SecurityAuditManager(SECURITY_AUDIT_REGISTRY)
    snapshot = manager.snapshot(3, _observations())
    first = manager.report(snapshot)
    second = manager.report(manager.snapshot(3, reversed(_observations())))
    assert first.to_json() == second.to_json()
    assert first.summary.health is SecurityHealth.HEALTHY
    assert first.compliance.compliant
    assert {metric.name for metric in first.metrics} == {
        "contracts",
        "boundaries",
        "policies",
        "violations",
        "incidents",
        "diagnostics",
        "audit_entries",
        "adoption_coverage",
        "runtime_coverage",
        "policy_coverage",
    }


def test_audit_detects_missing_declarations_and_incomplete_registry() -> None:
    incomplete = SecurityAuditRegistry(
        (SecurityAuditEntry("missing", boundary_contract="does-not-exist"),)
    )
    diagnostics = SecurityAuditManager(incomplete).audit(
        SecurityAuditManager(incomplete).snapshot(0)
    )
    assert {item.code for item in diagnostics.items} == {"MISSING_BOUNDARY_CONTRACT"}

    empty = SecurityAuditRegistry(())
    empty_diagnostics = SecurityAuditManager(empty).audit(SecurityAuditManager(empty).snapshot(0))
    assert {item.code for item in empty_diagnostics.items} == {"INCOMPLETE_REGISTRY"}


def test_audit_detects_violations_policies_adoption_and_contradictions() -> None:
    observations = (
        SecurityObservation(
            1,
            "duplicate",
            "adapter",
            SecurityObservationKind.VIOLATION,
            "unclassified",
            policy="unknown-policy",
            runtime_active=True,
        ),
        SecurityObservation(
            2,
            "duplicate",
            "adapter",
            SecurityObservationKind.DECISION,
            "unknown-decision",
        ),
    )
    manager = SecurityAuditManager(SECURITY_AUDIT_REGISTRY)
    report = manager.report(manager.snapshot(2, observations))
    codes = {item.code for item in report.diagnostics.items}
    assert codes == {
        "CONTRADICTORY_REPORT",
        "INCOHERENT_ADOPTION",
        "INCOMPATIBLE_POLICY",
        "UNCLASSIFIED_VIOLATION",
        "UNKNOWN_DECISION",
    }
    assert not report.compliance.compliant
    assert report.summary.health is SecurityHealth.DEGRADED


@pytest.mark.parametrize(
    ("factory", "error"),
    (
        (lambda: SecurityMetric("negative", -1), ValueError),
        (lambda: SecurityCoverage(10_001, 0, 0), ValueError),
        (
            lambda: SecurityAuditRegistry(
                (SecurityAuditEntry("x", runtime_policy="disabled"),) * 2
            ),
            ValueError,
        ),
    ),
)
def test_invalid_audit_models_are_rejected(
    factory: Callable[[], object], error: type[Exception]
) -> None:
    with pytest.raises(error):
        factory()
