"""Optional deterministic graceful-degradation runtime for EPIP.

Nothing in this module is activated automatically.  A caller must select a
contract, supply an explicit context, and invoke :class:`FallbackRuntime`.
The runtime never inspects exception messages and never reads a system clock.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.circuit_breaker import CircuitBreakerContract, CircuitBreakerState
from epip.core.exceptions import ExceptionContract
from epip.core.reliability import FailureContract, FailurePolicy
from epip.core.retry import RetryClassification, RetryContract


class FallbackPolicy(str, Enum):
    """Official explicit fallback policies."""

    FAIL = "fail"
    RETURN_DEFAULT = "return_default"
    RETURN_EMPTY = "return_empty"
    RETURN_LAST_KNOWN_VALUE = "return_last_known_value"
    RETURN_CACHED_VALUE = "return_cached_value"
    RETURN_DEGRADED_RESULT = "return_degraded_result"
    SKIP_OPERATION = "skip_operation"
    DISABLE_FEATURE = "disable_feature"
    READ_ONLY_MODE = "read_only_mode"
    CUSTOM = "custom"


class FallbackAction(str, Enum):
    """Concrete strategy selected by a fallback contract."""

    FAIL = "fail"
    CACHED_VALUE = "cached_value"
    LAST_KNOWN_VALUE = "last_known_value"
    SECONDARY_PROVIDER = "secondary_provider"
    SECONDARY_ADAPTER = "secondary_adapter"
    EMPTY_RESPONSE = "empty_response"
    DEFAULT_RESPONSE = "default_response"
    PARTIAL_RESPONSE = "partial_response"
    READ_ONLY_MODE = "read_only_mode"
    DEGRADED_MODE = "degraded_mode"
    DISABLED_MODE = "disabled_mode"
    SKIP_OPERATION = "skip_operation"
    MANUAL_FALLBACK = "manual_fallback"
    CUSTOM_FALLBACK = "custom_fallback"


class FallbackReason(str, Enum):
    """Machine-readable reasons for a fallback decision."""

    FAILURE_CLASSIFIED = "failure_classified"
    RETRIES_EXHAUSTED = "retries_exhausted"
    CIRCUIT_OPEN = "circuit_open"
    SERVICE_DEGRADED = "service_degraded"
    SERVICE_UNAVAILABLE = "service_unavailable"
    MANUAL_REQUEST = "manual_request"
    POLICY_FAIL = "policy_fail"


class AvailabilityLevel(str, Enum):
    """Official service-availability levels."""

    AVAILABLE = "available"
    DEGRADED = "degraded"
    LIMITED = "limited"
    UNAVAILABLE = "unavailable"
    READ_ONLY = "read_only"
    DISABLED = "disabled"
    UNKNOWN = "unknown"


class ServiceCapability(str, Enum):
    """Capabilities that may remain available during degradation."""

    READ = "read"
    WRITE = "write"
    CACHE_READ = "cache_read"
    HISTORICAL_READ = "historical_read"
    PRIMARY_PROVIDER = "primary_provider"
    SECONDARY_PROVIDER = "secondary_provider"
    PRIMARY_ADAPTER = "primary_adapter"
    SECONDARY_ADAPTER = "secondary_adapter"
    PARTIAL_RESULT = "partial_result"
    MANUAL_OPERATION = "manual_operation"


_POLICY_ACTIONS: Mapping[FallbackPolicy, frozenset[FallbackAction]] = MappingProxyType(
    {
        FallbackPolicy.FAIL: frozenset({FallbackAction.FAIL}),
        FallbackPolicy.RETURN_DEFAULT: frozenset({FallbackAction.DEFAULT_RESPONSE}),
        FallbackPolicy.RETURN_EMPTY: frozenset({FallbackAction.EMPTY_RESPONSE}),
        FallbackPolicy.RETURN_LAST_KNOWN_VALUE: frozenset({FallbackAction.LAST_KNOWN_VALUE}),
        FallbackPolicy.RETURN_CACHED_VALUE: frozenset({FallbackAction.CACHED_VALUE}),
        FallbackPolicy.RETURN_DEGRADED_RESULT: frozenset(
            {
                FallbackAction.SECONDARY_PROVIDER,
                FallbackAction.SECONDARY_ADAPTER,
                FallbackAction.PARTIAL_RESPONSE,
                FallbackAction.DEGRADED_MODE,
            }
        ),
        FallbackPolicy.SKIP_OPERATION: frozenset({FallbackAction.SKIP_OPERATION}),
        FallbackPolicy.DISABLE_FEATURE: frozenset({FallbackAction.DISABLED_MODE}),
        FallbackPolicy.READ_ONLY_MODE: frozenset({FallbackAction.READ_ONLY_MODE}),
        FallbackPolicy.CUSTOM: frozenset(
            {FallbackAction.MANUAL_FALLBACK, FallbackAction.CUSTOM_FALLBACK}
        ),
    }
)


@dataclass(frozen=True, slots=True)
class FallbackConfiguration:
    """Immutable limits and result-shape policy for one fallback."""

    history_limit: int = 100
    allow_partial_result: bool = False
    allow_empty_result: bool = False

    def __post_init__(self) -> None:
        if isinstance(self.history_limit, bool) or self.history_limit <= 0:
            raise ValueError("history limit must be a positive integer")
        if not isinstance(self.allow_partial_result, bool):
            raise TypeError("allow_partial_result must be a bool")
        if not isinstance(self.allow_empty_result, bool):
            raise TypeError("allow_empty_result must be a bool")


@dataclass(frozen=True, slots=True)
class FallbackContract:
    """Complete explicit degradation contract for one stable name."""

    name: str
    policy: FallbackPolicy
    action: FallbackAction
    degraded_availability: AvailabilityLevel
    remaining_capabilities: tuple[ServiceCapability, ...]
    disabled_features: tuple[str, ...]
    retry_contract: RetryContract
    failure_contract: FailureContract
    circuit_breaker_contract: CircuitBreakerContract
    exception_contract: ExceptionContract
    configuration: FallbackConfiguration
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("fallback contract name must be non-empty")
        if not isinstance(self.policy, FallbackPolicy):
            raise TypeError("fallback policy must be declared")
        if not isinstance(self.action, FallbackAction):
            raise TypeError("fallback action must be declared")
        if self.action not in _POLICY_ACTIONS[self.policy]:
            raise ValueError("fallback action is incompatible with policy")
        if not isinstance(self.degraded_availability, AvailabilityLevel):
            raise TypeError("degraded availability must be declared")
        capabilities = tuple(self.remaining_capabilities)
        if not all(isinstance(item, ServiceCapability) for item in capabilities):
            raise TypeError("remaining capabilities must be declared")
        if len(set(capabilities)) != len(capabilities):
            raise ValueError("remaining capabilities must be unique")
        disabled = tuple(self.disabled_features)
        if any(not item.strip() for item in disabled):
            raise ValueError("disabled feature names must be non-empty")
        if len(set(disabled)) != len(disabled):
            raise ValueError("disabled feature names must be unique")
        if not isinstance(self.retry_contract, RetryContract):
            raise TypeError("retry contract must be declared")
        if not isinstance(self.failure_contract, FailureContract):
            raise TypeError("failure contract must be declared")
        if not isinstance(self.circuit_breaker_contract, CircuitBreakerContract):
            raise TypeError("circuit-breaker contract must be declared")
        if not isinstance(self.exception_contract, ExceptionContract):
            raise TypeError("exception contract must be declared")
        if not isinstance(self.configuration, FallbackConfiguration):
            raise TypeError("fallback configuration must be declared")
        if not self.description.strip():
            raise ValueError("fallback description must be non-empty")
        object.__setattr__(self, "remaining_capabilities", capabilities)
        object.__setattr__(self, "disabled_features", disabled)


@dataclass(frozen=True, slots=True)
class FallbackContext:
    """Explicit deterministic inputs to one fallback evaluation."""

    logical_time: int
    availability: AvailabilityLevel
    circuit_state: CircuitBreakerState
    retries_exhausted: bool
    failure_classified: bool
    manual_request: bool = False
    default_value: object | None = None
    empty_value: object | None = None
    cached_value: object | None = None
    last_known_value: object | None = None
    degraded_value: object | None = None
    secondary_value: object | None = None
    custom_value: object | None = None

    def __post_init__(self) -> None:
        if isinstance(self.logical_time, bool) or self.logical_time < 0:
            raise ValueError("logical time must be a non-negative integer")
        if not isinstance(self.availability, AvailabilityLevel):
            raise TypeError("availability must be declared")
        if not isinstance(self.circuit_state, CircuitBreakerState):
            raise TypeError("circuit state must be declared")
        boolean_fields = (
            self.retries_exhausted,
            self.failure_classified,
            self.manual_request,
        )
        if not all(isinstance(item, bool) for item in boolean_fields):
            raise TypeError("fallback context flags must be bool values")


@dataclass(frozen=True, slots=True)
class FallbackDecision:
    """Immutable deterministic fallback decision."""

    apply: bool
    policy: FallbackPolicy
    action: FallbackAction
    reason: FallbackReason
    availability: AvailabilityLevel


@dataclass(frozen=True, slots=True)
class FallbackResult:
    """Immutable fallback outcome returned to an explicit adopter."""

    decision: FallbackDecision
    value: object | None
    partial: bool
    empty: bool
    skipped: bool


@dataclass(frozen=True, slots=True)
class FallbackStatistics:
    """Immutable fallback accounting."""

    evaluations: int = 0
    applied: int = 0
    rejected: int = 0
    degraded: int = 0


@dataclass(frozen=True, slots=True)
class FallbackSnapshot:
    """Immutable runtime snapshot with bounded logical history."""

    contract_name: str
    availability: AvailabilityLevel
    statistics: FallbackStatistics
    remaining_capabilities: tuple[ServiceCapability, ...]
    disabled_features: tuple[str, ...]
    history: tuple[tuple[int, FallbackAction, FallbackReason], ...]


@dataclass(frozen=True, slots=True)
class FallbackDiagnostics:
    """Deterministically ordered diagnostics."""

    messages: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether no diagnostic was recorded."""

        return not self.messages


@dataclass(frozen=True, slots=True)
class FallbackAudit:
    """Audit result for a fallback registry."""

    contracts_checked: int
    diagnostics: FallbackDiagnostics


@runtime_checkable
class FallbackAware(Protocol):
    """Protocol for explicit fallback adoption."""

    @property
    def fallback_contract(self) -> FallbackContract:
        """Return the explicitly adopted fallback contract."""


class FallbackRegistry(Mapping[str, FallbackContract]):
    """Immutable deterministic fallback contract registry."""

    __slots__ = ("_contracts",)

    def __init__(self, contracts: Iterable[FallbackContract]) -> None:
        items = tuple(contracts)
        mapping = {contract.name: contract for contract in items}
        if len(mapping) != len(items):
            raise ValueError("fallback contract names must be unique")
        self._contracts: Mapping[str, FallbackContract] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> FallbackContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, contract: str | FallbackAware) -> FallbackContract:
        """Resolve by stable name or explicitly aware object."""

        if not isinstance(contract, str) and isinstance(contract, FallbackAware):
            return contract.fallback_contract
        name = contract if isinstance(contract, str) else type(contract).__qualname__
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"no fallback contract declared for {name}") from error

    def declared(self) -> tuple[FallbackContract, ...]:
        """Return contracts in deterministic name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def audit(self, required: Iterable[str] = ()) -> FallbackAudit:
        """Return deterministic missing-contract diagnostics."""

        messages = tuple(
            f"missing fallback contract: {name}"
            for name in sorted(set(required) - self._contracts.keys())
        )
        return FallbackAudit(len(self), FallbackDiagnostics(messages))


_AVAILABILITY_TRANSITIONS: Mapping[AvailabilityLevel, frozenset[AvailabilityLevel]] = (
    MappingProxyType(
        {
            AvailabilityLevel.AVAILABLE: frozenset(
                {
                    AvailabilityLevel.DEGRADED,
                    AvailabilityLevel.LIMITED,
                    AvailabilityLevel.UNAVAILABLE,
                    AvailabilityLevel.READ_ONLY,
                    AvailabilityLevel.DISABLED,
                    AvailabilityLevel.UNKNOWN,
                }
            ),
            AvailabilityLevel.DEGRADED: frozenset(
                {
                    AvailabilityLevel.AVAILABLE,
                    AvailabilityLevel.LIMITED,
                    AvailabilityLevel.UNAVAILABLE,
                    AvailabilityLevel.READ_ONLY,
                    AvailabilityLevel.DISABLED,
                }
            ),
            AvailabilityLevel.LIMITED: frozenset(
                {
                    AvailabilityLevel.AVAILABLE,
                    AvailabilityLevel.DEGRADED,
                    AvailabilityLevel.UNAVAILABLE,
                    AvailabilityLevel.READ_ONLY,
                    AvailabilityLevel.DISABLED,
                }
            ),
            AvailabilityLevel.UNAVAILABLE: frozenset(
                {
                    AvailabilityLevel.AVAILABLE,
                    AvailabilityLevel.DEGRADED,
                    AvailabilityLevel.LIMITED,
                    AvailabilityLevel.DISABLED,
                }
            ),
            AvailabilityLevel.READ_ONLY: frozenset(
                {
                    AvailabilityLevel.AVAILABLE,
                    AvailabilityLevel.DEGRADED,
                    AvailabilityLevel.LIMITED,
                    AvailabilityLevel.UNAVAILABLE,
                    AvailabilityLevel.DISABLED,
                }
            ),
            AvailabilityLevel.DISABLED: frozenset(
                {AvailabilityLevel.AVAILABLE, AvailabilityLevel.UNKNOWN}
            ),
            AvailabilityLevel.UNKNOWN: frozenset(
                {
                    AvailabilityLevel.AVAILABLE,
                    AvailabilityLevel.DEGRADED,
                    AvailabilityLevel.LIMITED,
                    AvailabilityLevel.UNAVAILABLE,
                    AvailabilityLevel.READ_ONLY,
                    AvailabilityLevel.DISABLED,
                }
            ),
        }
    )
)


def transition_availability(
    current: AvailabilityLevel, target: AvailabilityLevel
) -> AvailabilityLevel:
    """Validate and return one deterministic availability transition."""

    if not isinstance(current, AvailabilityLevel) or not isinstance(target, AvailabilityLevel):
        raise TypeError("availability transition requires declared levels")
    if target not in _AVAILABILITY_TRANSITIONS[current]:
        raise ValueError(f"invalid availability transition: {current} -> {target}")
    return target


class FallbackRuntime:
    """Explicitly adopted deterministic fallback evaluator."""

    def __init__(self, contract: FallbackContract) -> None:
        if not isinstance(contract, FallbackContract):
            raise TypeError("contract must be a FallbackContract")
        self._contract = contract
        self._availability = AvailabilityLevel.AVAILABLE
        self._statistics = FallbackStatistics()
        self._history: tuple[tuple[int, FallbackAction, FallbackReason], ...] = ()
        self._logical_time = 0
        self._lock = RLock()

    def evaluate(self, context: FallbackContext) -> FallbackResult:
        """Evaluate and materialize the contract-selected fallback."""

        if not isinstance(context, FallbackContext):
            raise TypeError("context must be a FallbackContext")
        with self._lock:
            if context.logical_time < self._logical_time:
                raise ValueError("logical time must be monotonic")
            self._logical_time = context.logical_time
            reason = self._reason(context)
            apply = self._should_apply(context)
            target = self._contract.degraded_availability if apply else context.availability
            if target is not self._availability:
                self._availability = transition_availability(self._availability, target)
            decision = FallbackDecision(
                apply,
                self._contract.policy,
                self._contract.action,
                reason,
                self._availability,
            )
            value, partial, empty, skipped = self._materialize(context, apply)
            self._statistics = FallbackStatistics(
                self._statistics.evaluations + 1,
                self._statistics.applied + int(apply),
                self._statistics.rejected + int(not apply),
                self._statistics.degraded
                + int(apply and self._availability is not AvailabilityLevel.AVAILABLE),
            )
            self._history = (
                *self._history,
                (context.logical_time, self._contract.action, reason),
            )[-self._contract.configuration.history_limit :]
            return FallbackResult(decision, value, partial, empty, skipped)

    def _should_apply(self, context: FallbackContext) -> bool:
        if self._contract.policy is FallbackPolicy.FAIL:
            return False
        classified = context.failure_classified and self._official_failure()
        unavailable = context.availability in {
            AvailabilityLevel.DEGRADED,
            AvailabilityLevel.LIMITED,
            AvailabilityLevel.UNAVAILABLE,
            AvailabilityLevel.READ_ONLY,
            AvailabilityLevel.DISABLED,
        }
        circuit_open = context.circuit_state in {
            CircuitBreakerState.OPEN,
            CircuitBreakerState.FORCED_OPEN,
        }
        return context.manual_request or classified or unavailable or circuit_open

    def _official_failure(self) -> bool:
        failure = self._contract.failure_contract
        retry = self._contract.retry_contract
        exception = self._contract.exception_contract
        return failure.policy is not FailurePolicy.IGNORE and (
            retry.classification is not RetryClassification.NEVER_RETRY
            or exception.fatal
            or exception.retryable
        )

    def _reason(self, context: FallbackContext) -> FallbackReason:
        if self._contract.policy is FallbackPolicy.FAIL:
            return FallbackReason.POLICY_FAIL
        if context.manual_request:
            return FallbackReason.MANUAL_REQUEST
        if context.circuit_state in {CircuitBreakerState.OPEN, CircuitBreakerState.FORCED_OPEN}:
            return FallbackReason.CIRCUIT_OPEN
        if context.retries_exhausted:
            return FallbackReason.RETRIES_EXHAUSTED
        if context.failure_classified:
            return FallbackReason.FAILURE_CLASSIFIED
        if context.availability is AvailabilityLevel.UNAVAILABLE:
            return FallbackReason.SERVICE_UNAVAILABLE
        return FallbackReason.SERVICE_DEGRADED

    def _materialize(
        self, context: FallbackContext, apply: bool
    ) -> tuple[object | None, bool, bool, bool]:
        if not apply:
            return None, False, False, False
        action = self._contract.action
        if action is FallbackAction.CACHED_VALUE:
            return context.cached_value, False, False, False
        if action is FallbackAction.LAST_KNOWN_VALUE:
            return context.last_known_value, False, False, False
        if action in {FallbackAction.SECONDARY_PROVIDER, FallbackAction.SECONDARY_ADAPTER}:
            return context.secondary_value, False, False, False
        if action is FallbackAction.DEFAULT_RESPONSE:
            return context.default_value, False, False, False
        if action is FallbackAction.EMPTY_RESPONSE:
            if not self._contract.configuration.allow_empty_result:
                raise ValueError("empty response is not allowed by configuration")
            return context.empty_value, False, True, False
        if action is FallbackAction.PARTIAL_RESPONSE:
            if not self._contract.configuration.allow_partial_result:
                raise ValueError("partial response is not allowed by configuration")
            return context.degraded_value, True, False, False
        if action in {FallbackAction.DEGRADED_MODE, FallbackAction.READ_ONLY_MODE}:
            return context.degraded_value, False, False, False
        if action in {FallbackAction.MANUAL_FALLBACK, FallbackAction.CUSTOM_FALLBACK}:
            return context.custom_value, False, False, False
        if action in {FallbackAction.SKIP_OPERATION, FallbackAction.DISABLED_MODE}:
            return None, False, False, True
        return None, False, False, False

    def snapshot(self) -> FallbackSnapshot:
        """Return immutable bounded runtime diagnostics."""

        with self._lock:
            return FallbackSnapshot(
                self._contract.name,
                self._availability,
                self._statistics,
                self._contract.remaining_capabilities,
                self._contract.disabled_features,
                self._history,
            )


def _contract(
    name: str,
    policy: FallbackPolicy,
    action: FallbackAction,
    availability: AvailabilityLevel,
    capabilities: tuple[ServiceCapability, ...],
    disabled: tuple[str, ...] = (),
) -> FallbackContract:
    from epip.core.circuit_breaker import CIRCUIT_BREAKER_CONTRACTS
    from epip.core.exceptions import EXCEPTION_REGISTRY, ExternalSystemError
    from epip.core.reliability import RELIABILITY_CONTRACTS
    from epip.core.retry import RETRY_CONTRACTS

    failure = RELIABILITY_CONTRACTS["epip.core.external_effects.ExternalEffectContract"].failures[2]
    return FallbackContract(
        name,
        policy,
        action,
        availability,
        capabilities,
        disabled,
        RETRY_CONTRACTS["temporary_external_failure"],
        failure,
        CIRCUIT_BREAKER_CONTRACTS["external_boundary"],
        EXCEPTION_REGISTRY.resolve(ExternalSystemError),
        FallbackConfiguration(
            allow_partial_result=action is FallbackAction.PARTIAL_RESPONSE,
            allow_empty_result=action is FallbackAction.EMPTY_RESPONSE,
        ),
        f"Explicit {name.replace('_', ' ')} degradation strategy.",
    )


_CONTRACTS = (
    _contract("fail", FallbackPolicy.FAIL, FallbackAction.FAIL, AvailabilityLevel.UNAVAILABLE, ()),
    _contract(
        "cached_value",
        FallbackPolicy.RETURN_CACHED_VALUE,
        FallbackAction.CACHED_VALUE,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.READ, ServiceCapability.CACHE_READ),
    ),
    _contract(
        "last_known_value",
        FallbackPolicy.RETURN_LAST_KNOWN_VALUE,
        FallbackAction.LAST_KNOWN_VALUE,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.READ, ServiceCapability.HISTORICAL_READ),
    ),
    _contract(
        "secondary_provider",
        FallbackPolicy.RETURN_DEGRADED_RESULT,
        FallbackAction.SECONDARY_PROVIDER,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.READ, ServiceCapability.SECONDARY_PROVIDER),
        ("primary_provider",),
    ),
    _contract(
        "secondary_adapter",
        FallbackPolicy.RETURN_DEGRADED_RESULT,
        FallbackAction.SECONDARY_ADAPTER,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.READ, ServiceCapability.SECONDARY_ADAPTER),
        ("primary_adapter",),
    ),
    _contract(
        "empty_response",
        FallbackPolicy.RETURN_EMPTY,
        FallbackAction.EMPTY_RESPONSE,
        AvailabilityLevel.LIMITED,
        (ServiceCapability.READ,),
    ),
    _contract(
        "default_response",
        FallbackPolicy.RETURN_DEFAULT,
        FallbackAction.DEFAULT_RESPONSE,
        AvailabilityLevel.LIMITED,
        (ServiceCapability.READ,),
    ),
    _contract(
        "partial_response",
        FallbackPolicy.RETURN_DEGRADED_RESULT,
        FallbackAction.PARTIAL_RESPONSE,
        AvailabilityLevel.LIMITED,
        (ServiceCapability.READ, ServiceCapability.PARTIAL_RESULT),
    ),
    _contract(
        "read_only_mode",
        FallbackPolicy.READ_ONLY_MODE,
        FallbackAction.READ_ONLY_MODE,
        AvailabilityLevel.READ_ONLY,
        (ServiceCapability.READ,),
        ("write",),
    ),
    _contract(
        "degraded_mode",
        FallbackPolicy.RETURN_DEGRADED_RESULT,
        FallbackAction.DEGRADED_MODE,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.READ, ServiceCapability.PARTIAL_RESULT),
    ),
    _contract(
        "disabled_mode",
        FallbackPolicy.DISABLE_FEATURE,
        FallbackAction.DISABLED_MODE,
        AvailabilityLevel.DISABLED,
        (),
        ("feature",),
    ),
    _contract(
        "skip_operation",
        FallbackPolicy.SKIP_OPERATION,
        FallbackAction.SKIP_OPERATION,
        AvailabilityLevel.LIMITED,
        (ServiceCapability.READ,),
    ),
    _contract(
        "manual_fallback",
        FallbackPolicy.CUSTOM,
        FallbackAction.MANUAL_FALLBACK,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.MANUAL_OPERATION,),
    ),
    _contract(
        "custom_fallback",
        FallbackPolicy.CUSTOM,
        FallbackAction.CUSTOM_FALLBACK,
        AvailabilityLevel.DEGRADED,
        (ServiceCapability.MANUAL_OPERATION,),
    ),
)

DEGRADATION_CONTRACTS = FallbackRegistry(_CONTRACTS)


def get_fallback_contract(contract: str | FallbackAware) -> FallbackContract:
    """Resolve an official fallback contract."""

    return DEGRADATION_CONTRACTS.resolve(contract)


def declared_fallback_contracts() -> tuple[FallbackContract, ...]:
    """Return official fallback contracts deterministically."""

    return DEGRADATION_CONTRACTS.declared()


__all__ = [
    "DEGRADATION_CONTRACTS",
    "AvailabilityLevel",
    "FallbackAction",
    "FallbackAudit",
    "FallbackAware",
    "FallbackConfiguration",
    "FallbackContext",
    "FallbackContract",
    "FallbackDecision",
    "FallbackDiagnostics",
    "FallbackPolicy",
    "FallbackReason",
    "FallbackRegistry",
    "FallbackResult",
    "FallbackRuntime",
    "FallbackSnapshot",
    "FallbackStatistics",
    "ServiceCapability",
    "declared_fallback_contracts",
    "get_fallback_contract",
    "transition_availability",
]
