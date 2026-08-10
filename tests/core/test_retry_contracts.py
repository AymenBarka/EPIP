"""Acceptance tests for declarative retry contracts."""

from dataclasses import FrozenInstanceError

import pytest

from epip.core.reliability import FailureResponsibility
from epip.core.retry import (
    RETRY_CONTRACTS,
    JitterPolicy,
    RetryClassification,
    RetryCondition,
    RetryConfiguration,
    RetryContract,
    RetryPolicy,
    RetryRegistry,
    RetryTrigger,
    declared_retry_contracts,
    get_retry_contract,
)


def configuration(**overrides: object) -> RetryConfiguration:
    values: dict[str, object] = {
        "maximum_attempts": 3,
        "maximum_elapsed_duration": 30.0,
        "initial_delay": 1.0,
        "maximum_delay": 10.0,
        "backoff_coefficient": 2.0,
        "delay_cap": 10.0,
        "retry_budget": 3,
        "jitter_policy": JitterPolicy.NONE,
    }
    values.update(overrides)
    return RetryConfiguration(**values)  # type: ignore[arg-type]


def contract(name: str = "test") -> RetryContract:
    return RetryContract(
        name,
        RetryPolicy.EXPONENTIAL_BACKOFF,
        (RetryCondition.TIMEOUT,),
        RetryClassification.CONDITIONALLY_RETRYABLE,
        FailureResponsibility.CALLER,
        configuration(),
        "test contract",
    )


def test_registry_is_complete_deterministic_and_resolvable() -> None:
    contracts = declared_retry_contracts()
    assert contracts == tuple(sorted(contracts, key=lambda item: item.name))
    assert {item.conditions[0] for item in contracts} == set(RetryCondition)
    assert get_retry_contract("timeout") is RETRY_CONTRACTS["timeout"]
    with pytest.raises(LookupError, match="no retry contract"):
        get_retry_contract("unknown")


def test_contracts_and_configurations_are_immutable() -> None:
    item = get_retry_contract("timeout")
    with pytest.raises(FrozenInstanceError):
        item.description = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.configuration.retry_budget = 99  # type: ignore[misc]


def test_all_strategies_jitter_modes_classifications_and_triggers_are_declared() -> None:
    assert {item.value for item in RetryPolicy} == {
        "no_retry",
        "immediate",
        "fixed_delay",
        "linear_backoff",
        "exponential_backoff",
        "exponential_with_cap",
        "custom",
    }
    assert len(JitterPolicy) == 5
    assert len(RetryClassification) == 7
    assert len(RetryTrigger) == 5


@pytest.mark.parametrize(
    ("field", "value", "message"),
    (
        ("maximum_attempts", -1, "maximum attempts"),
        ("maximum_elapsed_duration", -1.0, "maximum elapsed duration"),
        ("initial_delay", -1.0, "initial delay"),
        ("maximum_delay", -1.0, "maximum delay"),
        ("backoff_coefficient", 0.0, "backoff coefficient"),
        ("delay_cap", -1.0, "delay cap"),
        ("retry_budget", -1, "retry budget"),
    ),
)
def test_invalid_limits_and_budgets_are_rejected(field: str, value: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        configuration(**{field: value})


def test_delay_cannot_exceed_cap() -> None:
    with pytest.raises(ValueError, match="delay cap"):
        configuration(maximum_delay=11.0)


def test_incomplete_and_incoherent_contracts_are_rejected() -> None:
    with pytest.raises(ValueError, match="condition"):
        RetryContract(
            "incomplete",
            RetryPolicy.IMMEDIATE,
            (),
            RetryClassification.RETRYABLE,
            FailureResponsibility.FRAMEWORK,
            configuration(),
            "missing condition",
        )
    with pytest.raises(ValueError, match="NO_RETRY"):
        RetryContract(
            "contradictory",
            RetryPolicy.IMMEDIATE,
            (RetryCondition.FATAL_ERROR,),
            RetryClassification.NEVER_RETRY,
            FailureResponsibility.FRAMEWORK,
            configuration(),
            "invalid policy",
        )


def test_no_retry_requires_zero_attempts_and_budget() -> None:
    with pytest.raises(ValueError, match="zero attempts"):
        RetryContract(
            "invalid-disabled",
            RetryPolicy.NO_RETRY,
            (RetryCondition.VALIDATION_ERROR,),
            RetryClassification.NEVER_RETRY,
            FailureResponsibility.CALLER,
            configuration(),
            "invalid disabled contract",
        )


def test_registry_rejects_duplicates_and_audits_missing_contracts() -> None:
    item = contract()
    with pytest.raises(ValueError, match="unique"):
        RetryRegistry((item, item))
    audit = RetryRegistry((item,)).audit(("test", "missing"))
    assert audit.contracts_checked == 1
    assert audit.diagnostics.messages == ("missing retry contract: missing",)
    assert not audit.diagnostics.valid
    assert RETRY_CONTRACTS.audit().diagnostics.valid
