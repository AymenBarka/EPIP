from __future__ import annotations

from dataclasses import FrozenInstanceError

import pytest

from epip.core.runtime_security import (
    RUNTIME_SECURITY_POLICIES,
    RuntimeSecurityAdapter,
    RuntimeSecurityAdoption,
    RuntimeSecurityAudit,
    RuntimeSecurityContext,
    RuntimeSecurityDecision,
    RuntimeSecurityManager,
    RuntimeSecurityPolicy,
    RuntimeSecurityRegistry,
    RuntimeSecurityStatistics,
    RuntimeSecurityViolation,
    SecurityPolicyBinding,
    SecurityPolicyConfiguration,
    SecurityPolicyScope,
    declared_runtime_security_policies,
    get_runtime_security_policy,
)


def _binding(
    *,
    binding_id: str = "portfolio-call",
    policy_name: str = "strict",
    scope: SecurityPolicyScope = SecurityPolicyScope.CALL,
    target: str = "PortfolioEngine.update",
    security_contracts: tuple[str, ...] = (),
) -> SecurityPolicyBinding:
    return SecurityPolicyBinding(
        binding_id=binding_id,
        policy_name=policy_name,
        scope=scope,
        target=target,
        security_contracts=security_contracts,
    )


def _adoption(
    policy: RuntimeSecurityPolicy = RuntimeSecurityPolicy.STRICT,
    *,
    enabled: bool = True,
    explicitly_adopted: bool = True,
    binding: SecurityPolicyBinding | None = None,
    custom_policy_name: str | None = None,
) -> RuntimeSecurityAdoption:
    return RuntimeSecurityAdoption(
        binding or _binding(policy_name=policy.value),
        SecurityPolicyConfiguration(
            policy,
            enabled=enabled,
            custom_policy_name=custom_policy_name,
        ),
        explicitly_adopted=explicitly_adopted,
    )


def _context() -> RuntimeSecurityContext:
    return RuntimeSecurityContext(
        "PortfolioEngine",
        "update",
        SecurityPolicyScope.CALL,
        attributes={"z": "last", "a": "first"},
    )


def test_official_registry_is_complete_inert_and_deterministic() -> None:
    entries = declared_runtime_security_policies()
    assert tuple(name for name, _ in entries) == tuple(
        sorted(policy.value for policy in RuntimeSecurityPolicy)
    )
    assert {configuration.policy for _, configuration in entries} == set(RuntimeSecurityPolicy)
    assert all(not configuration.enabled for _, configuration in entries)
    assert get_runtime_security_policy("strict").policy is RuntimeSecurityPolicy.STRICT
    with pytest.raises(TypeError):
        RUNTIME_SECURITY_POLICIES.policies["new"] = SecurityPolicyConfiguration(  # type: ignore[index]
            RuntimeSecurityPolicy.STRICT
        )
    with pytest.raises(LookupError):
        get_runtime_security_policy("missing")


def test_models_are_immutable_and_normalize_order() -> None:
    binding = SecurityPolicyBinding(
        "id",
        "strict",
        SecurityPolicyScope.CALL,
        "operation",
        security_contracts=("z", "a"),
    )
    context = _context()
    assert binding.security_contracts == ("a", "z")
    assert tuple(context.attributes) == ("a", "z")
    with pytest.raises(FrozenInstanceError):
        binding.target = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError):
        context.attributes["new"] = "value"  # type: ignore[index]
    with pytest.raises(ValueError):
        _binding(binding_id=" ")
    with pytest.raises(ValueError):
        RuntimeSecurityContext("", "call", SecurityPolicyScope.CALL)


@pytest.mark.parametrize(
    ("policy", "violations", "expected"),
    [
        (RuntimeSecurityPolicy.NO_SECURITY, True, RuntimeSecurityDecision.IGNORE),
        (RuntimeSecurityPolicy.DISABLED, True, RuntimeSecurityDecision.IGNORE),
        (RuntimeSecurityPolicy.MONITOR_ONLY, True, RuntimeSecurityDecision.REPORT_ONLY),
        (RuntimeSecurityPolicy.VALIDATE_ONLY, True, RuntimeSecurityDecision.DENY),
        (RuntimeSecurityPolicy.VALIDATE_AND_REPORT, True, RuntimeSecurityDecision.DENY),
        (RuntimeSecurityPolicy.STRICT, True, RuntimeSecurityDecision.DENY),
        (RuntimeSecurityPolicy.STRICT, False, RuntimeSecurityDecision.ALLOW),
        (RuntimeSecurityPolicy.CUSTOM, True, RuntimeSecurityDecision.DELEGATE),
    ],
)
def test_policy_decisions_are_deterministic(
    policy: RuntimeSecurityPolicy,
    violations: bool,
    expected: RuntimeSecurityDecision,
) -> None:
    adoption = _adoption(
        policy,
        custom_policy_name="owner.policy" if policy is RuntimeSecurityPolicy.CUSTOM else None,
    )
    supplied = (RuntimeSecurityViolation("blocked", "blocked input"),) if violations else ()
    first = RuntimeSecurityAdapter.evaluate(adoption, _context(), supplied)
    second = RuntimeSecurityAdapter.evaluate(adoption, _context(), supplied)
    assert first == second
    assert first.decision is expected


def test_inactive_adoption_never_enforces() -> None:
    violation = RuntimeSecurityViolation("x", "observed")
    for adoption in (
        _adoption(enabled=False),
        _adoption(explicitly_adopted=False),
    ):
        result = RuntimeSecurityAdapter.evaluate(adoption, _context(), (violation,))
        assert result.decision is RuntimeSecurityDecision.IGNORE


def test_manager_requires_explicit_adoption_and_produces_snapshot() -> None:
    manager = RuntimeSecurityManager()
    assert manager.snapshot().adoptions == ()
    with pytest.raises(ValueError):
        manager.adopt(_adoption(explicitly_adopted=False))
    manager.adopt(_adoption())
    with pytest.raises(ValueError):
        manager.adopt(_adoption())
    violation = RuntimeSecurityViolation("range", "outside declared range")
    result = manager.evaluate("portfolio-call", _context(), (violation,))
    snapshot = manager.snapshot()
    assert result.decision is RuntimeSecurityDecision.DENY
    assert snapshot.sequence == 2
    assert snapshot.results == (result,)
    assert snapshot.statistics == RuntimeSecurityStatistics(
        evaluations=1,
        denied=1,
        violations=1,
    )
    manager.revoke("portfolio-call")
    assert manager.snapshot().adoptions == ()
    with pytest.raises(LookupError):
        manager.evaluate("portfolio-call", _context())
    with pytest.raises(LookupError):
        manager.revoke("portfolio-call")


def test_audit_reports_all_diagnostic_categories() -> None:
    registry = RuntimeSecurityRegistry(
        {"strict": SecurityPolicyConfiguration(RuntimeSecurityPolicy.STRICT)}
    )
    duplicate = _adoption(
        RuntimeSecurityPolicy.MONITOR_ONLY,
        binding=_binding(
            binding_id="duplicate",
            policy_name="strict",
            scope=SecurityPolicyScope.GLOBAL,
            target="wrong",
            security_contracts=("unknown-contract",),
        ),
    )
    missing = _adoption(binding=_binding(binding_id="duplicate", policy_name="absent"))
    custom = _adoption(
        RuntimeSecurityPolicy.CUSTOM,
        binding=_binding(binding_id="custom", policy_name="strict"),
    )
    violation = RuntimeSecurityViolation("invalid", "typed violation")
    diagnostics = RuntimeSecurityAudit.inspect(
        registry,
        (duplicate, missing, custom),
        security_contracts=("known",),
        violations=(violation,),
    )
    assert not diagnostics.valid
    assert diagnostics.missing_policies == ("absent",)
    assert diagnostics.incompatible_policies == ("custom", "duplicate")
    assert diagnostics.invalid_bindings == ("duplicate binding: duplicate",)
    assert diagnostics.incoherent_scopes == ("duplicate",)
    assert diagnostics.incompatible_contracts == ("security:unknown-contract",)
    assert diagnostics.invalid_configurations == ("custom",)
    assert diagnostics.typed_violations == (violation,)


def test_audit_detects_incomplete_registry_and_valid_adoption() -> None:
    empty = RuntimeSecurityRegistry({})
    incomplete = RuntimeSecurityAudit.inspect(empty, ())
    assert incomplete.incomplete_registry == ("registry is empty",)
    valid = RuntimeSecurityAudit.inspect(
        RUNTIME_SECURITY_POLICIES,
        (_adoption(),),
    )
    assert valid.valid


def test_invalid_configuration_and_violation_values_are_rejected() -> None:
    with pytest.raises(ValueError):
        RuntimeSecurityViolation("", "message")
    with pytest.raises(ValueError):
        RuntimeSecurityRegistry({" ": SecurityPolicyConfiguration(RuntimeSecurityPolicy.STRICT)})


def test_statistics_cover_every_decision() -> None:
    results = tuple(
        RuntimeSecurityAdapter.evaluate(
            _adoption(
                (
                    RuntimeSecurityPolicy.CUSTOM
                    if decision is RuntimeSecurityDecision.DELEGATE
                    else RuntimeSecurityPolicy.STRICT
                ),
                enabled=decision is not RuntimeSecurityDecision.IGNORE,
                custom_policy_name=(
                    "custom" if decision is RuntimeSecurityDecision.DELEGATE else None
                ),
            ),
            _context(),
        )
        for decision in (
            RuntimeSecurityDecision.ALLOW,
            RuntimeSecurityDecision.DELEGATE,
            RuntimeSecurityDecision.IGNORE,
        )
    )
    statistics = RuntimeSecurityStatistics.from_results(results)
    assert statistics.evaluations == 3
    assert (statistics.allowed, statistics.delegated, statistics.ignored) == (1, 1, 1)
