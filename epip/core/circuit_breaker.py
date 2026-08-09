"""Optional deterministic circuit-breaker runtime for EPIP.

Nothing in this module is adopted automatically.  Callers must construct and
invoke a circuit breaker explicitly.  Logical time is supplied by the caller;
the implementation never reads a system clock.
"""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from threading import RLock
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.exceptions import ExceptionContract
from epip.core.reliability import FailureContract, FailurePolicy
from epip.core.retry import RetryClassification, RetryContract


class CircuitBreakerState(str, Enum):
    """Official circuit-breaker states."""

    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"
    FORCED_OPEN = "forced_open"
    DISABLED = "disabled"


class FailureIsolation(str, Enum):
    """Explicit isolation boundary owned by a circuit breaker."""

    PROVIDER = "provider"
    ADAPTER = "adapter"
    PLUGIN = "plugin"
    EXTERNAL_BOUNDARY = "external_boundary"
    COMPONENT = "component"
    CALLER = "caller"


@dataclass(frozen=True, slots=True)
class CircuitBreakerConfiguration:
    """Immutable thresholds for one circuit-breaker instance."""

    failure_threshold: int
    success_threshold: int
    window_size: int
    minimum_samples: int
    failure_ratio_threshold: float
    logical_open_duration: int
    half_open_max_trials: int
    half_open_failure_threshold: int

    def __post_init__(self) -> None:
        integer_fields = (
            ("failure threshold", self.failure_threshold),
            ("success threshold", self.success_threshold),
            ("window size", self.window_size),
            ("minimum samples", self.minimum_samples),
            ("logical open duration", self.logical_open_duration),
            ("half-open maximum trials", self.half_open_max_trials),
            ("half-open failure threshold", self.half_open_failure_threshold),
        )
        if any(isinstance(value, bool) or value <= 0 for _, value in integer_fields):
            invalid = next(
                name for name, value in integer_fields if isinstance(value, bool) or value <= 0
            )
            raise ValueError(f"{invalid} must be a positive integer")
        if self.minimum_samples > self.window_size:
            raise ValueError("minimum samples cannot exceed window size")
        if not 0.0 < self.failure_ratio_threshold <= 1.0:
            raise ValueError("failure ratio threshold must be in (0, 1]")
        if self.success_threshold > self.half_open_max_trials:
            raise ValueError("success threshold cannot exceed half-open maximum trials")
        if self.half_open_failure_threshold > self.half_open_max_trials:
            raise ValueError("failure threshold cannot exceed half-open maximum trials")


@dataclass(frozen=True, slots=True)
class CircuitBreakerContract:
    """Declarative adoption contract for one isolation boundary."""

    name: str
    isolation: FailureIsolation
    configuration: CircuitBreakerConfiguration
    retry_contract: RetryContract
    failure_contract: FailureContract
    exception_contract: ExceptionContract
    description: str

    def __post_init__(self) -> None:
        if not self.name.strip():
            raise ValueError("circuit-breaker contract name must be non-empty")
        if not isinstance(self.isolation, FailureIsolation):
            raise TypeError("failure isolation must be declared")
        if not isinstance(self.configuration, CircuitBreakerConfiguration):
            raise TypeError("circuit-breaker configuration must be declared")
        if not isinstance(self.retry_contract, RetryContract):
            raise TypeError("retry contract must be declared")
        if not isinstance(self.failure_contract, FailureContract):
            raise TypeError("failure contract must be declared")
        if not isinstance(self.exception_contract, ExceptionContract):
            raise TypeError("exception contract must be declared")
        if not self.description.strip():
            raise ValueError("circuit-breaker description must be non-empty")


@dataclass(frozen=True, slots=True)
class FailureCounter:
    """Failure accounting at one logical instant."""

    total: int = 0
    consecutive: int = 0


@dataclass(frozen=True, slots=True)
class SuccessCounter:
    """Success accounting at one logical instant."""

    total: int = 0
    consecutive: int = 0


@dataclass(frozen=True, slots=True)
class FailureWindow:
    """Immutable rolling logical outcome window."""

    outcomes: tuple[bool, ...] = ()

    def append(self, failed: bool, maximum_size: int) -> FailureWindow:
        """Return a new window bounded to ``maximum_size`` outcomes."""

        if maximum_size <= 0:
            raise ValueError("window size must be positive")
        return FailureWindow((*self.outcomes, failed)[-maximum_size:])

    @property
    def failure_ratio(self) -> float:
        """Return the observed failure ratio, or zero for an empty window."""

        return sum(self.outcomes) / len(self.outcomes) if self.outcomes else 0.0


@dataclass(frozen=True, slots=True)
class CircuitBreakerDecision:
    """Immutable permit decision for a caller operation."""

    permitted: bool
    state: CircuitBreakerState
    reason: str


@dataclass(frozen=True, slots=True)
class CircuitBreakerStatistics:
    """Immutable aggregate counters."""

    failures: FailureCounter
    successes: SuccessCounter
    half_open_trials: int
    failure_ratio: float


@dataclass(frozen=True, slots=True)
class CircuitBreakerSnapshot:
    """Immutable diagnostic snapshot of circuit-breaker state."""

    name: str
    state: CircuitBreakerState
    logical_time: int
    statistics: CircuitBreakerStatistics
    reason: str
    history: tuple[tuple[CircuitBreakerState, str], ...]


@dataclass(frozen=True, slots=True)
class CircuitBreakerDiagnostics:
    """Deterministically ordered circuit-breaker diagnostics."""

    messages: tuple[str, ...] = ()

    @property
    def valid(self) -> bool:
        """Return whether no diagnostic was recorded."""

        return not self.messages


@dataclass(frozen=True, slots=True)
class CircuitBreakerAudit:
    """Audit result for a circuit-breaker registry."""

    contracts_checked: int
    diagnostics: CircuitBreakerDiagnostics


class FailureClassifier:
    """Classify failures exclusively through H006 contracts."""

    @staticmethod
    def counts_as_failure(
        retry: RetryContract,
        failure: FailureContract,
        exception: ExceptionContract,
    ) -> bool:
        """Return whether the explicit contracts classify an isolatable failure."""

        if not all(
            (
                isinstance(retry, RetryContract),
                isinstance(failure, FailureContract),
                isinstance(exception, ExceptionContract),
            )
        ):
            raise TypeError("failure classification requires all three H006 contracts")
        if failure.policy is FailurePolicy.IGNORE:
            return False
        return retry.classification is not RetryClassification.NEVER_RETRY or exception.fatal


@runtime_checkable
class CircuitBreakerAware(Protocol):
    """Protocol for explicit circuit-breaker adoption."""

    @property
    def circuit_breaker_contract(self) -> CircuitBreakerContract:
        """Return the explicitly adopted circuit-breaker contract."""


class CircuitBreakerRegistry(Mapping[str, CircuitBreakerContract]):
    """Immutable deterministic circuit-breaker contract registry."""

    __slots__ = ("_contracts",)

    def __init__(self, contracts: Iterable[CircuitBreakerContract]) -> None:
        items = tuple(contracts)
        mapping = {contract.name: contract for contract in items}
        if len(mapping) != len(items):
            raise ValueError("circuit-breaker contract names must be unique")
        self._contracts: Mapping[str, CircuitBreakerContract] = MappingProxyType(mapping)

    def __getitem__(self, key: str) -> CircuitBreakerContract:
        return self._contracts[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._contracts)

    def __len__(self) -> int:
        return len(self._contracts)

    def resolve(self, contract: str | CircuitBreakerAware) -> CircuitBreakerContract:
        """Resolve by stable name or explicitly aware object."""

        if not isinstance(contract, str) and isinstance(contract, CircuitBreakerAware):
            return contract.circuit_breaker_contract
        name = contract if isinstance(contract, str) else type(contract).__qualname__
        try:
            return self._contracts[name]
        except KeyError as error:
            raise LookupError(f"no circuit-breaker contract declared for {name}") from error

    def declared(self) -> tuple[CircuitBreakerContract, ...]:
        """Return contracts in deterministic name order."""

        return tuple(self._contracts[name] for name in sorted(self._contracts))

    def audit(self, required: Iterable[str] = ()) -> CircuitBreakerAudit:
        """Return deterministic missing-contract diagnostics."""

        messages = tuple(
            f"missing circuit-breaker contract: {name}"
            for name in sorted(set(required) - self._contracts.keys())
        )
        return CircuitBreakerAudit(len(self), CircuitBreakerDiagnostics(messages))


_ALLOWED_TRANSITIONS: Mapping[CircuitBreakerState, frozenset[CircuitBreakerState]] = (
    MappingProxyType(
        {
            CircuitBreakerState.CLOSED: frozenset(
                {
                    CircuitBreakerState.OPEN,
                    CircuitBreakerState.FORCED_OPEN,
                    CircuitBreakerState.DISABLED,
                }
            ),
            CircuitBreakerState.OPEN: frozenset(
                {
                    CircuitBreakerState.HALF_OPEN,
                    CircuitBreakerState.FORCED_OPEN,
                    CircuitBreakerState.DISABLED,
                }
            ),
            CircuitBreakerState.HALF_OPEN: frozenset(
                {
                    CircuitBreakerState.CLOSED,
                    CircuitBreakerState.OPEN,
                    CircuitBreakerState.FORCED_OPEN,
                    CircuitBreakerState.DISABLED,
                }
            ),
            CircuitBreakerState.FORCED_OPEN: frozenset(
                {CircuitBreakerState.CLOSED, CircuitBreakerState.DISABLED}
            ),
            CircuitBreakerState.DISABLED: frozenset(
                {CircuitBreakerState.CLOSED, CircuitBreakerState.FORCED_OPEN}
            ),
        }
    )
)


class CircuitBreaker:
    """Explicitly adopted deterministic circuit-breaker state machine."""

    def __init__(self, contract: CircuitBreakerContract) -> None:
        if not isinstance(contract, CircuitBreakerContract):
            raise TypeError("contract must be a CircuitBreakerContract")
        self._contract = contract
        self._state = CircuitBreakerState.CLOSED
        self._failures = FailureCounter()
        self._successes = SuccessCounter()
        self._window = FailureWindow()
        self._half_open_trials = 0
        self._opened_at: int | None = None
        self._logical_time = 0
        self._reason = "initialized closed"
        self._history: tuple[tuple[CircuitBreakerState, str], ...] = ((self._state, self._reason),)
        self._lock = RLock()

    @property
    def state(self) -> CircuitBreakerState:
        """Return the current state."""

        with self._lock:
            return self._state

    def transition(self, target: CircuitBreakerState, reason: str) -> None:
        """Apply an explicit valid transition."""

        if not isinstance(target, CircuitBreakerState):
            raise TypeError("target must be a CircuitBreakerState")
        if not reason.strip():
            raise ValueError("transition reason must be non-empty")
        with self._lock:
            self._transition(target, reason)

    def _transition(self, target: CircuitBreakerState, reason: str) -> None:
        if target not in _ALLOWED_TRANSITIONS[self._state]:
            raise ValueError(f"invalid circuit-breaker transition: {self._state} -> {target}")
        self._state = target
        self._reason = reason
        self._history = (*self._history, (target, reason))
        if target is CircuitBreakerState.OPEN:
            self._opened_at = self._logical_time
            self._half_open_trials = 0
        elif target in {CircuitBreakerState.CLOSED, CircuitBreakerState.DISABLED}:
            self._opened_at = None
            self._half_open_trials = 0
            if target is CircuitBreakerState.CLOSED:
                self._failures = FailureCounter(self._failures.total, 0)
                self._successes = SuccessCounter(self._successes.total, 0)

    def allow(self, logical_time: int) -> CircuitBreakerDecision:
        """Return whether a caller operation is permitted at logical time."""

        if isinstance(logical_time, bool) or logical_time < 0:
            raise ValueError("logical time must be a non-negative integer")
        with self._lock:
            if logical_time < self._logical_time:
                raise ValueError("logical time must be monotonic")
            self._logical_time = logical_time
            if (
                self._state is CircuitBreakerState.OPEN
                and self._opened_at is not None
                and logical_time - self._opened_at
                >= self._contract.configuration.logical_open_duration
            ):
                self._transition(CircuitBreakerState.HALF_OPEN, "logical open duration elapsed")
            if self._state is CircuitBreakerState.DISABLED:
                return CircuitBreakerDecision(True, self._state, "circuit breaker disabled")
            if self._state in {CircuitBreakerState.OPEN, CircuitBreakerState.FORCED_OPEN}:
                return CircuitBreakerDecision(False, self._state, self._reason)
            if (
                self._state is CircuitBreakerState.HALF_OPEN
                and self._half_open_trials >= self._contract.configuration.half_open_max_trials
            ):
                return CircuitBreakerDecision(False, self._state, "half-open trial limit reached")
            if self._state is CircuitBreakerState.HALF_OPEN:
                self._half_open_trials += 1
            return CircuitBreakerDecision(True, self._state, "operation permitted")

    def record_failure(self, reason: str, logical_time: int) -> None:
        """Record one explicitly classified failure."""

        if not reason.strip():
            raise ValueError("failure reason must be non-empty")
        if not FailureClassifier.counts_as_failure(
            self._contract.retry_contract,
            self._contract.failure_contract,
            self._contract.exception_contract,
        ):
            return
        with self._lock:
            self._logical_time = max(self._logical_time, logical_time)
            self._failures = FailureCounter(
                self._failures.total + 1, self._failures.consecutive + 1
            )
            self._successes = SuccessCounter(self._successes.total, 0)
            self._window = self._window.append(True, self._contract.configuration.window_size)
            if self._state is CircuitBreakerState.HALF_OPEN:
                if (
                    self._failures.consecutive
                    >= self._contract.configuration.half_open_failure_threshold
                ):
                    self._transition(CircuitBreakerState.OPEN, f"reopened: {reason}")
            elif self._state is CircuitBreakerState.CLOSED and self._should_open():
                self._transition(CircuitBreakerState.OPEN, f"opened: {reason}")

    def record_success(self, reason: str, logical_time: int) -> None:
        """Record one successful operation."""

        if not reason.strip():
            raise ValueError("success reason must be non-empty")
        with self._lock:
            self._logical_time = max(self._logical_time, logical_time)
            self._successes = SuccessCounter(
                self._successes.total + 1, self._successes.consecutive + 1
            )
            self._failures = FailureCounter(self._failures.total, 0)
            self._window = self._window.append(False, self._contract.configuration.window_size)
            if (
                self._state is CircuitBreakerState.HALF_OPEN
                and self._successes.consecutive >= self._contract.configuration.success_threshold
            ):
                self._transition(CircuitBreakerState.CLOSED, f"closed: {reason}")

    def _should_open(self) -> bool:
        enough_samples = len(self._window.outcomes) >= self._contract.configuration.minimum_samples
        return self._failures.consecutive >= self._contract.configuration.failure_threshold or (
            enough_samples
            and self._window.failure_ratio >= self._contract.configuration.failure_ratio_threshold
        )

    def snapshot(self) -> CircuitBreakerSnapshot:
        """Return an immutable snapshot without exposing business state."""

        with self._lock:
            statistics = CircuitBreakerStatistics(
                self._failures,
                self._successes,
                self._half_open_trials,
                self._window.failure_ratio,
            )
            return CircuitBreakerSnapshot(
                self._contract.name,
                self._state,
                self._logical_time,
                statistics,
                self._reason,
                self._history,
            )


def _contract(name: str, isolation: FailureIsolation) -> CircuitBreakerContract:
    from epip.core.exceptions import EXCEPTION_REGISTRY, ExternalSystemError
    from epip.core.reliability import RELIABILITY_CONTRACTS
    from epip.core.retry import RETRY_CONTRACTS

    failure = RELIABILITY_CONTRACTS["epip.core.external_effects.ExternalEffectContract"].failures[2]
    return CircuitBreakerContract(
        name,
        isolation,
        CircuitBreakerConfiguration(3, 2, 10, 3, 0.5, 5, 3, 1),
        RETRY_CONTRACTS["temporary_external_failure"],
        failure,
        EXCEPTION_REGISTRY.resolve(ExternalSystemError),
        f"Optional {isolation.value.replace('_', ' ')} failure isolation.",
    )


_CONTRACTS = tuple(_contract(item.value, item) for item in FailureIsolation)
CIRCUIT_BREAKER_CONTRACTS = CircuitBreakerRegistry(_CONTRACTS)


def get_circuit_breaker_contract(
    contract: str | CircuitBreakerAware,
) -> CircuitBreakerContract:
    """Resolve an official circuit-breaker contract."""

    return CIRCUIT_BREAKER_CONTRACTS.resolve(contract)


def declared_circuit_breakers() -> tuple[CircuitBreakerContract, ...]:
    """Return official circuit-breaker contracts deterministically."""

    return CIRCUIT_BREAKER_CONTRACTS.declared()


__all__ = [
    "CIRCUIT_BREAKER_CONTRACTS",
    "CircuitBreaker",
    "CircuitBreakerAudit",
    "CircuitBreakerAware",
    "CircuitBreakerConfiguration",
    "CircuitBreakerContract",
    "CircuitBreakerDecision",
    "CircuitBreakerDiagnostics",
    "CircuitBreakerRegistry",
    "CircuitBreakerSnapshot",
    "CircuitBreakerState",
    "CircuitBreakerStatistics",
    "FailureClassifier",
    "FailureCounter",
    "FailureIsolation",
    "FailureWindow",
    "SuccessCounter",
    "declared_circuit_breakers",
    "get_circuit_breaker_contract",
]
