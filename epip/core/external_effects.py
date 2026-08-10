"""Official contracts for EPIP external-effect boundaries.

The declarations are descriptive. They deliberately do not provide distributed
transactions, retries, compensation, or exactly-once delivery.
"""

from __future__ import annotations

from collections.abc import Mapping
from enum import StrEnum
from types import MappingProxyType
from typing import NamedTuple

from epip.core.concurrency import ThreadSafetyLevel


class ExternalBoundary(StrEnum):
    """External integration boundaries recognized by EPIP."""

    EXTERNAL_EVENT_BUS = "external_event_bus"
    FEATURE_PROVIDER = "feature_provider"
    MARKET_DATA_PROVIDER = "market_data_provider"
    MT5 = "mt5"
    TWELVE_DATA = "twelve_data"
    PAPER_ADAPTER = "paper_adapter"
    BROKER_ADAPTER = "broker_adapter"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    LOGGING = "logging"
    SYSTEM_CLOCK = "system_clock"
    SYSTEM_IDENTITY = "system_identity"
    USER_CALLBACK = "user_callback"


class ExternalEffectNature(StrEnum):
    """Kind of interaction performed across a boundary."""

    READ = "read"
    WRITE = "write"
    READ_WRITE = "read_write"
    PUBLICATION = "publication"
    CALLBACK = "callback"
    OBSERVATION = "observation"


class IdempotencyLevel(StrEnum):
    """Idempotence guarantee offered by one integration."""

    IDEMPOTENT = "idempotent"
    CONDITIONAL = "conditional"
    NON_IDEMPOTENT = "non_idempotent"


class DeliveryGuarantee(StrEnum):
    """Delivery guarantee available at an external boundary."""

    NOT_APPLICABLE = "not_applicable"
    BEST_EFFORT = "best_effort"
    AT_LEAST_ONCE_WITH_CALLER_RETRY = "at_least_once_with_caller_retry"


class ExternalFailurePolicy(StrEnum):
    """Framework response to an external failure."""

    PROPAGATE = "propagate"
    TRANSLATE_AND_PROPAGATE = "translate_and_propagate"
    BEST_EFFORT = "best_effort"


class ExternalEffectContract(NamedTuple):
    """Immutable declaration of one external-effect boundary."""

    boundary: ExternalBoundary
    nature: ExternalEffectNature
    responsibility: str
    thread_safety: ThreadSafetyLevel
    transactional: bool
    compensable: bool
    idempotency: IdempotencyLevel
    deterministic: bool
    delivery: DeliveryGuarantee
    failure_policy: ExternalFailurePolicy
    execution_order: str
    observability: str
    rollback: str
    restrictions: tuple[str, ...]


def _effect(
    boundary: ExternalBoundary,
    nature: ExternalEffectNature,
    responsibility: str,
    thread_safety: ThreadSafetyLevel,
    *,
    transactional: bool = False,
    compensable: bool = False,
    idempotency: IdempotencyLevel = IdempotencyLevel.NON_IDEMPOTENT,
    deterministic: bool = False,
    delivery: DeliveryGuarantee = DeliveryGuarantee.NOT_APPLICABLE,
    failure_policy: ExternalFailurePolicy = ExternalFailurePolicy.PROPAGATE,
    execution_order: str,
    observability: str,
    rollback: str = "No rollback is provided by EPIP.",
    restrictions: tuple[str, ...],
) -> ExternalEffectContract:
    return ExternalEffectContract(
        boundary,
        nature,
        responsibility,
        thread_safety,
        transactional,
        compensable,
        idempotency,
        deterministic,
        delivery,
        failure_policy,
        execution_order,
        observability,
        rollback,
        restrictions,
    )


_CONTRACTS = (
    _effect(
        ExternalBoundary.EXTERNAL_EVENT_BUS,
        ExternalEffectNature.PUBLICATION,
        "EPIP orders local dispatch; external subscribers own their side effects.",
        ThreadSafetyLevel.THREAD_SAFE,
        delivery=DeliveryGuarantee.BEST_EFFORT,
        execution_order="After the owning local transaction commits.",
        observability="Accepted events remain in local EventBus history.",
        restrictions=("Listener completion is not a distributed commit.",),
    ),
    _effect(
        ExternalBoundary.FEATURE_PROVIDER,
        ExternalEffectNature.READ,
        "The provider owns calculation or retrieval; FeatureStore owns local commit.",
        ThreadSafetyLevel.THREAD_SAFE,
        idempotency=IdempotencyLevel.CONDITIONAL,
        deterministic=True,
        execution_order="Inside FeatureStore preparation, before cache commit.",
        observability="Only a completed FeatureSet enters cache and history.",
        restrictions=("Concrete providers may declare a stronger restriction.",),
    ),
    _effect(
        ExternalBoundary.MARKET_DATA_PROVIDER,
        ExternalEffectNature.READ_WRITE,
        "The provider owns connection lifecycle and source reads.",
        ThreadSafetyLevel.THREAD_CONFINED,
        idempotency=IdempotencyLevel.CONDITIONAL,
        execution_order="Connection precedes reads; disconnect follows caller use.",
        observability="Failures are translated to the market-data exception hierarchy.",
        failure_policy=ExternalFailurePolicy.TRANSLATE_AND_PROPAGATE,
        restrictions=("Do not overlap lifecycle changes and reads.",),
    ),
    _effect(
        ExternalBoundary.MT5,
        ExternalEffectNature.READ_WRITE,
        "The MT5 client owns terminal, network, and broker-side state.",
        ThreadSafetyLevel.THREAD_CONFINED,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        delivery=DeliveryGuarantee.AT_LEAST_ONCE_WITH_CALLER_RETRY,
        execution_order="Adapter invocation occurs before any dependent local commit.",
        observability="Adapter responses and translated failures are observable.",
        restrictions=("Exactly-once orders require broker idempotency keys not supplied by EPIP.",),
    ),
    _effect(
        ExternalBoundary.TWELVE_DATA,
        ExternalEffectNature.READ,
        "The remote API owns availability, throttling, and returned market data.",
        ThreadSafetyLevel.THREAD_CONFINED,
        idempotency=IdempotencyLevel.CONDITIONAL,
        execution_order="Remote read completes before provider cache mutation.",
        observability="Provider errors are propagated through the market-data boundary.",
        restrictions=("Timeout and retry policy belong to the concrete adapter.",),
    ),
    _effect(
        ExternalBoundary.PAPER_ADAPTER,
        ExternalEffectNature.WRITE,
        "EPIP owns the in-memory paper sequence and synthetic fill response.",
        ThreadSafetyLevel.THREAD_SAFE,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        deterministic=True,
        execution_order="The serialized adapter call precedes ExecutionEngine commit.",
        observability="The returned BrokerResponse is the complete observable effect.",
        restrictions=("Repeated submit calls create distinct synthetic fills.",),
    ),
    _effect(
        ExternalBoundary.BROKER_ADAPTER,
        ExternalEffectNature.WRITE,
        "The broker owns order acceptance, fills, cancellation, and settlement.",
        ThreadSafetyLevel.THREAD_CONFINED,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        delivery=DeliveryGuarantee.AT_LEAST_ONCE_WITH_CALLER_RETRY,
        execution_order="Broker response is obtained before ExecutionEngine state commit.",
        observability="Responses or broker exceptions cross the adapter protocol.",
        restrictions=("Retry can duplicate an order unless the broker deduplicates it.",),
    ),
    _effect(
        ExternalBoundary.FILESYSTEM,
        ExternalEffectNature.READ_WRITE,
        "The operating system owns access, durability, locking, and atomic replacement.",
        ThreadSafetyLevel.THREAD_COMPATIBLE,
        idempotency=IdempotencyLevel.CONDITIONAL,
        execution_order="I/O must complete before data is accepted into local state.",
        observability="I/O exceptions or translated ProviderError values are observable.",
        restrictions=("EPIP provides no cross-process filesystem transaction.",),
    ),
    _effect(
        ExternalBoundary.NETWORK,
        ExternalEffectNature.READ_WRITE,
        "The adapter and remote endpoint own transport and remote state.",
        ThreadSafetyLevel.THREAD_CONFINED,
        idempotency=IdempotencyLevel.CONDITIONAL,
        delivery=DeliveryGuarantee.BEST_EFFORT,
        execution_order="Defined by the concrete provider or broker adapter.",
        observability="Timeouts and transport failures must cross the adapter boundary.",
        restrictions=("A timeout does not prove that the remote effect did not occur.",),
    ),
    _effect(
        ExternalBoundary.LOGGING,
        ExternalEffectNature.OBSERVATION,
        "Logging handlers own formatting, transport, and persistence.",
        ThreadSafetyLevel.THREAD_COMPATIBLE,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        delivery=DeliveryGuarantee.BEST_EFFORT,
        failure_policy=ExternalFailurePolicy.BEST_EFFORT,
        execution_order="Diagnostic only; never part of a business commit decision.",
        observability="Handler behavior depends on Python logging configuration.",
        restrictions=("Log delivery and uniqueness are not guaranteed.",),
    ),
    _effect(
        ExternalBoundary.SYSTEM_CLOCK,
        ExternalEffectNature.READ,
        "The operating system owns wall-clock accuracy and monotonic adjustments.",
        ThreadSafetyLevel.THREAD_SAFE,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        execution_order="Read when technical metadata requires a timestamp.",
        observability="The produced timestamp is stored explicitly where required.",
        restrictions=(
            "System time is non-deterministic; inject a deterministic clock for replay.",
        ),
    ),
    _effect(
        ExternalBoundary.SYSTEM_IDENTITY,
        ExternalEffectNature.READ,
        "The operating system UUID source owns entropy and uniqueness quality.",
        ThreadSafetyLevel.THREAD_SAFE,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        execution_order="Generated when explicit technical identity is absent.",
        observability="The generated identity is persisted in the created object.",
        restrictions=(
            "System identities are non-deterministic; inject a deterministic generator.",
        ),
    ),
    _effect(
        ExternalBoundary.USER_CALLBACK,
        ExternalEffectNature.CALLBACK,
        "The callback owner is responsible for callback state and external effects.",
        ThreadSafetyLevel.NOT_THREAD_SAFE,
        idempotency=IdempotencyLevel.NON_IDEMPOTENT,
        delivery=DeliveryGuarantee.BEST_EFFORT,
        execution_order="After listener snapshot capture and outside EPIP state locks.",
        observability="Exceptions propagate to the publisher according to EventBus policy.",
        restrictions=("Callbacks must provide their own synchronization and idempotence.",),
    ),
)

EXTERNAL_EFFECT_CONTRACTS: Mapping[ExternalBoundary, ExternalEffectContract] = MappingProxyType(
    {contract.boundary: contract for contract in _CONTRACTS}
)


def external_effect_contract(boundary: ExternalBoundary) -> ExternalEffectContract:
    """Return the official immutable contract for an external boundary."""
    return EXTERNAL_EFFECT_CONTRACTS[boundary]
