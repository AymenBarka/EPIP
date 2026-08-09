"""Declarative retry policies and contracts for EPIP.

This module describes retry eligibility, ownership, limits, and diagnostics.
It deliberately contains no retry loop, sleeping, randomness, or runtime
integration.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.reliability import FailureResponsibility


class RetryPolicy(str, Enum):
    """Supported declarative retry strategies."""

    NO_RETRY = "no_retry"
    IMMEDIATE = "immediate"
    FIXED_DELAY = "fixed_delay"
    LINEAR_BACKOFF = "linear_backoff"
    EXPONENTIAL_BACKOFF = "exponential_backoff"
    EXPONENTIAL_WITH_CAP = "exponential_with_cap"
    CUSTOM = "custom"


class RetryCondition(str, Enum):
    """Conditions that may participate in a retry decision."""

    RETRYABLE_EXCEPTION = "retryable_exception"
    NON_RETRYABLE_EXCEPTION = "non_retryable_exception"
    TIMEOUT = "timeout"
    TEMPORARY_EXTERNAL_FAILURE = "temporary_external_failure"
    RESOURCE_UNAVAILABLE = "resource_unavailable"
    PROVIDER_UNAVAILABLE = "provider_unavailable"
    NETWORK_INTERRUPTION = "network_interruption"
    USER_CANCELLATION = "user_cancellation"
    CONFIGURATION_ERROR = "configuration_error"
    VALIDATION_ERROR = "validation_error"
    FATAL_ERROR = "fatal_error"


class RetryTrigger(str, Enum):
    """Origin of a declarative retry evaluation."""

    EXCEPTION = "exception"
    TIMEOUT = "timeout"
    AVAILABILITY = "availability"
    INTERRUPTION = "interruption"
    CALLER_REQUEST = "caller_request"


class RetryClassification(str, Enum):
    """Ownership and eligibility classification for retry behaviour."""

    RETRYABLE = "retryable"
    NON_RETRYABLE = "non_retryable"
    CONDITIONALLY_RETRYABLE = "conditionally_retryable"
    NEVER_RETRY = "never_retry"
    EXTERNAL_RETRY_ONLY = "external_retry_only"
    FRAMEWORK_RETRY = "framework_retry"
    CALLER_RETRY = "caller_retry"


class JitterPolicy(str, Enum):
    """Declared jitter policy; no random delay is calculated here."""

    NONE = "none"
    FIXED = "fixed"
    FULL = "full"
    EQUAL = "equal"
    DECORRELATED = "decorrelated"


@dataclass(frozen=True, slots=True)
class RetryConfiguration:
    """Immutable descriptive limits for a retry contract."""

    maximum_attempts: int
    maximum_elapsed_duration: float
    initial_delay: float
    maximum_delay: float
    backoff_coefficient: float
    delay_cap: float
    retry_budget: int
    jitter_policy: JitterPolicy

    def __post_init__(self) -> None:
        if isinstance(self.maximum_attempts, bool) or self.maximum_attempts < 0:
            raise ValueError("maximum attempts must be a non-negative integer")
        if isinstance(self.retry_budget, bool) or self.retry_budget < 0:
            raise ValueError("retry budget must be a non-negative integer")
        numeric = (
            ("maximum elapsed duration", self.maximum_elapsed_duration),
            ("initial delay", self.initial_delay),
            ("maximum delay", self.maximum_delay),
            ("delay cap", self.delay_cap),
        )
        if any(value < 0 for _, value in numeric):
            invalid = next(name for name, value in numeric if value < 0)
            raise ValueError(f"{invalid} must be non-negative")
        if self.backoff_coefficient <= 0:
            raise ValueError("backoff coefficient must be positive")
        if self.maximum_delay > self.delay_cap:
            raise ValueError("maximum delay cannot exceed delay cap")
        if not isinstance(self.jitter_policy, JitterPolicy):
            raise TypeError("jitter policy must be a JitterPolicy")


@dataclass(frozen=True, slots=True)
class RetryContract:
    """Complete retry declaration for one stable contract name."""

    name: str
    policy: RetryPolicy
    conditions: tuple[RetryCondition, ...]
    classification: RetryClassification
    responsibility: FailureResponsibility
    configuration: RetryConfiguration
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("retry contract name must be non-empty")
        if not isinstance(self.policy, RetryPolicy):
            raise TypeError("retry strategy must be declared")
        conditions = tuple(self.conditions)
        if not conditions or not all(isinstance(item, RetryCondition) for item in conditions):
            raise ValueError("at least one valid retry condition must be declared")
        if len(set(conditions)) != len(conditions):
            raise ValueError("retry conditions must be unique")
        if not isinstance(self.classification, RetryClassification):
            raise TypeError("retry classification must be declared")
        if not isinstance(self.responsibility, FailureResponsibility):
            raise TypeError("retry responsibility must be declared")
        if not isinstance(self.configuration, RetryConfiguration):
            raise TypeError("retry configuration must be declared")
        if not self.description.strip():
            raise ValueError("retry contract description must be non-empty")
        disabled = self.classification in {
            RetryClassification.NON_RETRYABLE,
            RetryClassification.NEVER_RETRY,
        }
        if disabled and self.policy is not RetryPolicy.NO_RETRY:
            raise ValueError("non-retryable classifications require NO_RETRY")
        if self.policy is RetryPolicy.NO_RETRY and (
            self.configuration.maximum_attempts != 0 or self.configuration.retry_budget != 0
        ):
            raise ValueError("NO_RETRY contracts require zero attempts and budget")
        object.__setattr__(self, "conditions", conditions)


@dataclass(frozen=True, slots=True)
class RetryContext:
    """Descriptive input to a future retry decision engine."""

    contract_name: str
    trigger: RetryTrigger
    condition: RetryCondition
    attempt_number: int
    elapsed_duration: float


@dataclass(frozen=True, slots=True)
class RetryDecision:
    """Immutable record of a declarative retry decision."""

    retry: bool
    responsibility: FailureResponsibility
    reason: str


@dataclass(frozen=True, slots=True)
class RetryAttempt:
    """Immutable description of one potential retry attempt."""

    number: int
    delay: float
    trigger: RetryTrigger


@dataclass(frozen=True, slots=True)
class RetryResult:
    """Immutable descriptive outcome; it does not execute an operation."""

    decision: RetryDecision
    attempt: RetryAttempt | None
    exhausted: bool


@dataclass(frozen=True, slots=True)
class RetryStatistics:
    """Immutable aggregate retry counters."""

    evaluated: int = 0
    approved: int = 0
    rejected: int = 0
    exhausted: int = 0


@dataclass(frozen=True, slots=True)
class RetryDiagnostics:
    """Deterministically ordered retry contract diagnostics."""

    messages: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether no diagnostic was recorded."""

        return not self.messages


@dataclass(frozen=True, slots=True)
class RetryAudit:
    """Audit result for a retry registry."""

    contracts_checked: int
    diagnostics: RetryDiagnostics


@runtime_checkable
class RetryAware(Protocol):
    """Protocol for components that explicitly expose a retry contract."""

    @property
    def retry_contract(self) -> RetryContract:
        """Return the component's immutable retry contract."""


class RetryRegistry(Mapping[str, RetryContract]):
    """Immutable, deterministic registry of retry contracts."""

    __slots__ = ("_contracts",)

    def __init__(self, contracts: Iterable[RetryContract]) -> None:
        items = tuple(contracts)
        mapping = {contract.name: contract for contract in items}
        if len(mapping) != len(items):
            raise ValueError("retry contract names must be unique")
        self._contracts: Mapping[str, RetryContract] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> RetryContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, contract: str | RetryAware) -> RetryContract:
        """Resolve a contract by stable name or RetryAware object."""

        if not isinstance(contract, str) and isinstance(contract, RetryAware):
            return contract.retry_contract
        name = contract if isinstance(contract, str) else type(contract).__qualname__
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"no retry contract declared for {name}") from error

    def declared(self) -> tuple[RetryContract, ...]:
        """Return contracts in deterministic name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def audit(self, required: Iterable[str] = ()) -> RetryAudit:
        """Return deterministic diagnostics for absent declarations."""

        messages = tuple(
            f"missing retry contract: {name}"
            for name in sorted(set(required) - self._contracts.keys())
        )
        return RetryAudit(len(self), RetryDiagnostics(messages))


_DISABLED = RetryConfiguration(0, 0.0, 0.0, 0.0, 1.0, 0.0, 0, JitterPolicy.NONE)
_IMMEDIATE = RetryConfiguration(3, 30.0, 0.0, 0.0, 1.0, 0.0, 3, JitterPolicy.NONE)
_EXTERNAL = RetryConfiguration(5, 120.0, 1.0, 30.0, 2.0, 30.0, 5, JitterPolicy.FULL)


def _contract(
    name: str,
    policy: RetryPolicy,
    condition: RetryCondition,
    classification: RetryClassification,
    responsibility: FailureResponsibility,
    configuration: RetryConfiguration,
) -> RetryContract:
    return RetryContract(
        name,
        policy,
        (condition,),
        classification,
        responsibility,
        configuration,
        f"Official declarative policy for {condition.value.replace('_', ' ')}.",
    )


_CONTRACTS = (
    _contract(
        "retryable_exception",
        RetryPolicy.IMMEDIATE,
        RetryCondition.RETRYABLE_EXCEPTION,
        RetryClassification.FRAMEWORK_RETRY,
        FailureResponsibility.FRAMEWORK,
        _IMMEDIATE,
    ),
    _contract(
        "non_retryable_exception",
        RetryPolicy.NO_RETRY,
        RetryCondition.NON_RETRYABLE_EXCEPTION,
        RetryClassification.NON_RETRYABLE,
        FailureResponsibility.CALLER,
        _DISABLED,
    ),
    _contract(
        "timeout",
        RetryPolicy.EXPONENTIAL_WITH_CAP,
        RetryCondition.TIMEOUT,
        RetryClassification.CONDITIONALLY_RETRYABLE,
        FailureResponsibility.CALLER,
        _EXTERNAL,
    ),
    _contract(
        "temporary_external_failure",
        RetryPolicy.EXPONENTIAL_BACKOFF,
        RetryCondition.TEMPORARY_EXTERNAL_FAILURE,
        RetryClassification.EXTERNAL_RETRY_ONLY,
        FailureResponsibility.EXTERNAL_SYSTEM,
        _EXTERNAL,
    ),
    _contract(
        "resource_unavailable",
        RetryPolicy.LINEAR_BACKOFF,
        RetryCondition.RESOURCE_UNAVAILABLE,
        RetryClassification.CONDITIONALLY_RETRYABLE,
        FailureResponsibility.OPERATING_SYSTEM,
        _EXTERNAL,
    ),
    _contract(
        "provider_unavailable",
        RetryPolicy.FIXED_DELAY,
        RetryCondition.PROVIDER_UNAVAILABLE,
        RetryClassification.CALLER_RETRY,
        FailureResponsibility.PROVIDER,
        _EXTERNAL,
    ),
    _contract(
        "network_interruption",
        RetryPolicy.EXPONENTIAL_WITH_CAP,
        RetryCondition.NETWORK_INTERRUPTION,
        RetryClassification.EXTERNAL_RETRY_ONLY,
        FailureResponsibility.OPERATING_SYSTEM,
        _EXTERNAL,
    ),
    _contract(
        "user_cancellation",
        RetryPolicy.NO_RETRY,
        RetryCondition.USER_CANCELLATION,
        RetryClassification.NEVER_RETRY,
        FailureResponsibility.USER,
        _DISABLED,
    ),
    _contract(
        "configuration_error",
        RetryPolicy.NO_RETRY,
        RetryCondition.CONFIGURATION_ERROR,
        RetryClassification.NEVER_RETRY,
        FailureResponsibility.USER,
        _DISABLED,
    ),
    _contract(
        "validation_error",
        RetryPolicy.NO_RETRY,
        RetryCondition.VALIDATION_ERROR,
        RetryClassification.NEVER_RETRY,
        FailureResponsibility.CALLER,
        _DISABLED,
    ),
    _contract(
        "fatal_error",
        RetryPolicy.NO_RETRY,
        RetryCondition.FATAL_ERROR,
        RetryClassification.NEVER_RETRY,
        FailureResponsibility.FRAMEWORK,
        _DISABLED,
    ),
)

RETRY_CONTRACTS = RetryRegistry(_CONTRACTS)


def get_retry_contract(contract: str | RetryAware) -> RetryContract:
    """Resolve an official retry contract without executing a retry."""

    return RETRY_CONTRACTS.resolve(contract)


def declared_retry_contracts() -> tuple[RetryContract, ...]:
    """Return official retry contracts in deterministic order."""

    return RETRY_CONTRACTS.declared()


__all__ = [
    "RETRY_CONTRACTS",
    "JitterPolicy",
    "RetryAttempt",
    "RetryAudit",
    "RetryAware",
    "RetryClassification",
    "RetryCondition",
    "RetryConfiguration",
    "RetryContext",
    "RetryContract",
    "RetryDecision",
    "RetryDiagnostics",
    "RetryPolicy",
    "RetryRegistry",
    "RetryResult",
    "RetryStatistics",
    "RetryTrigger",
    "declared_retry_contracts",
    "get_retry_contract",
]
