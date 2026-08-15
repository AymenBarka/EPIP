"""Immutable EPIP-017 producer capability and execution contracts.

Blueprint ownership: Programme A Blueprint v1.1, Work Package A02.
ADR ownership: ADR-EPIP017-02 under the boundary constraints of
ADR-EPIP017-01.  The module validates declarations and immutable producer
envelopes only.  Downstream authorities remain unimplemented.
"""

from __future__ import annotations

from dataclasses import dataclass, fields, is_dataclass
from enum import Enum
from types import MappingProxyType
from typing import Protocol, runtime_checkable

from epip.core.integrity import DataIntegrityError, deep_freeze, require_text

_SUCCESS_OUTCOMES = frozenset({"success", "valid_empty"})
_FAILURE_OUTCOMES = frozenset(
    {
        "input_validation_failure",
        "unsupported_contract_or_capability",
        "invalid_configuration",
        "invalid_context_projection",
        "dependency_unavailable",
        "dependency_semantically_invalid",
        "unsupported_temporal_boundary",
        "analytical_execution_failure",
        "deterministic_contract_violation",
        "cooperative_cancellation",
    }
)
_OUTCOMES = _SUCCESS_OUTCOMES | _FAILURE_OUTCOMES


def _require_strings(values: tuple[str, ...], field: str, *, required: bool = False) -> None:
    if required and not values:
        raise DataIntegrityError(f"{field} must not be empty")
    if any(not isinstance(value, str) or not value.strip() for value in values):
        raise DataIntegrityError(f"{field} must contain non-empty strings")
    if len(set(values)) != len(values):
        raise DataIntegrityError(f"{field} must not contain duplicates")


def _freeze_strings(
    values: tuple[str, ...], field: str, *, required: bool = False
) -> tuple[str, ...]:
    frozen = tuple(values)
    _require_strings(frozen, field, required=required)
    return frozen


def _require_boolean(value: object, field: str) -> None:
    if not isinstance(value, bool):
        raise DataIntegrityError(f"{field} must be boolean")


def _freeze_pairs(
    values: tuple[tuple[str, object], ...], field: str
) -> tuple[tuple[str, object], ...]:
    names = tuple(name for name, _ in values)
    _require_strings(names, field)
    frozen = tuple((name, deep_freeze(value)) for name, value in values)
    for _, value in frozen:
        _require_deeply_immutable(value, field)
    return frozen


def _require_capability_references(values: tuple[tuple[str, str], ...], field: str) -> None:
    if not values:
        raise DataIntegrityError(f"{field} must not be empty")
    if any(not identity.strip() or not version.strip() for identity, version in values):
        raise DataIntegrityError(f"{field} must contain complete identity and version pairs")
    if len(set(values)) != len(values):
        raise DataIntegrityError(f"{field} must not contain duplicates")


def _require_deeply_immutable(value: object, field: str) -> None:
    if value is None or isinstance(value, (bool, int, float, str, bytes, Enum)):
        return
    if isinstance(value, tuple | frozenset):
        for item in value:
            _require_deeply_immutable(item, field)
        return
    if isinstance(value, MappingProxyType):
        for key, item in value.items():
            _require_deeply_immutable(key, field)
            _require_deeply_immutable(item, field)
        return
    if is_dataclass(value) and getattr(type(value), "__dataclass_params__").frozen:  # noqa: B009
        for item in fields(value):
            _require_deeply_immutable(getattr(value, item.name), field)
        return
    raise DataIntegrityError(f"{field} contains mutable or unsupported state")


@dataclass(frozen=True, slots=True)
class ProducerCapability:
    """Blueprint v1.1 A02 capability governed by ADR-01 and ADR-02."""

    identity: str
    version: str
    category: str
    accepted_input_semantics: tuple[str, ...]
    produced_output_semantics: tuple[str, ...]
    required_dependencies: tuple[str, ...]
    optional_dependencies: tuple[str, ...]
    context_fields: tuple[str, ...]
    temporal_requirements: tuple[str, ...]
    output_schema_version: str
    valid_empty_supported: bool
    compatibility_claims: tuple[str, ...]
    certification_obligations: tuple[str, ...]
    atomic_semantic_group: bool = False

    def __post_init__(self) -> None:
        """Validate the immutable ADR-02 capability declaration."""

        for name in (
            "accepted_input_semantics",
            "produced_output_semantics",
            "required_dependencies",
            "optional_dependencies",
            "context_fields",
            "temporal_requirements",
            "compatibility_claims",
            "certification_obligations",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        _require_boolean(self.valid_empty_supported, "capability.valid_empty_supported")
        _require_boolean(self.atomic_semantic_group, "capability.atomic_semantic_group")
        _validate_capability_contract(self)


@dataclass(frozen=True, slots=True)
class ProducerExecutionEnvironment:
    """Blueprint v1.1 A02 granted environment governed by ADR-01 and ADR-02."""

    execution_profile: str
    isolation_profile: str
    resource_profile: str
    cancellation_requested: bool
    control_signals: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Reject undeclared or malformed execution-control declarations."""

        require_text(self.execution_profile, "environment.execution_profile")
        require_text(self.isolation_profile, "environment.isolation_profile")
        require_text(self.resource_profile, "environment.resource_profile")
        _require_boolean(
            self.cancellation_requested,
            "environment.cancellation_requested",
        )
        object.__setattr__(
            self,
            "control_signals",
            _freeze_strings(self.control_signals, "environment.control_signals"),
        )


@dataclass(frozen=True, slots=True)
class ProducerExecutionInput:
    """Blueprint v1.1 A02 immutable input governed by ADR-01 and ADR-02."""

    manifest_reference: str
    producer_identity: str
    producer_version: str
    contract_version: str
    selected_capabilities: tuple[tuple[str, str], ...]
    input_schema_version: str
    configuration_schema_version: str
    configuration: tuple[tuple[str, object], ...]
    context_schema_version: str
    context_source_authority: str
    context_projection: tuple[tuple[str, object], ...]
    dependencies: tuple[tuple[str, object], ...]
    symbol: str
    timeframe: str
    temporal_boundary: str
    data_revision: str
    registry_snapshot_reference: str
    semantic_plan_reference: str
    replay_boundary_reference: str | None = None
    logical_clock_value: str | None = None

    def __post_init__(self) -> None:
        """Freeze granted values and reject malformed A02 input envelopes."""

        for name in (
            "manifest_reference",
            "producer_identity",
            "producer_version",
            "contract_version",
            "input_schema_version",
            "configuration_schema_version",
            "context_schema_version",
            "context_source_authority",
            "symbol",
            "timeframe",
            "temporal_boundary",
            "data_revision",
            "registry_snapshot_reference",
            "semantic_plan_reference",
        ):
            require_text(getattr(self, name), f"execution_input.{name}")
        selected_capabilities = tuple(
            (identity, version) for identity, version in self.selected_capabilities
        )
        object.__setattr__(self, "selected_capabilities", selected_capabilities)
        _require_capability_references(
            selected_capabilities,
            "execution_input.selected_capabilities",
        )
        for name in ("replay_boundary_reference", "logical_clock_value"):
            value = getattr(self, name)
            if value is not None:
                require_text(value, f"execution_input.{name}")
        object.__setattr__(
            self,
            "configuration",
            _freeze_pairs(self.configuration, "execution_input.configuration"),
        )
        object.__setattr__(
            self,
            "context_projection",
            _freeze_pairs(self.context_projection, "execution_input.context_projection"),
        )
        object.__setattr__(
            self,
            "dependencies",
            _freeze_pairs(self.dependencies, "execution_input.dependencies"),
        )


@dataclass(frozen=True, slots=True)
class ProducerExecutionOutput:
    """Blueprint v1.1 A02 candidate output governed by ADR-01 and ADR-02."""

    input_manifest_reference: str
    producer_identity: str
    producer_version: str
    contract_version: str
    capability_references: tuple[tuple[str, str], ...]
    output_schema_version: str
    diagnostic_schema_version: str
    failure_schema_version: str
    outcome: str
    evidence_outputs: tuple[tuple[str, object], ...] = ()
    semantic_metadata: tuple[tuple[str, object], ...] = ()
    semantic_diagnostics: tuple[tuple[str, str], ...] = ()
    semantic_statistics: tuple[tuple[str, object], ...] = ()
    semantic_trace_facts: tuple[tuple[str, object], ...] = ()

    def __post_init__(self) -> None:
        """Freeze result content and enforce terminal A02 outcome distinctions."""

        for name in (
            "input_manifest_reference",
            "producer_identity",
            "producer_version",
            "contract_version",
            "output_schema_version",
            "diagnostic_schema_version",
            "failure_schema_version",
            "outcome",
        ):
            require_text(getattr(self, name), f"execution_output.{name}")
        capability_references = tuple(
            (identity, version) for identity, version in self.capability_references
        )
        object.__setattr__(self, "capability_references", capability_references)
        _require_capability_references(
            capability_references,
            "execution_output.capability_references",
        )
        if self.outcome not in _OUTCOMES:
            raise DataIntegrityError("execution_output.outcome is not declared by ADR-02")
        object.__setattr__(
            self,
            "evidence_outputs",
            _freeze_pairs(self.evidence_outputs, "execution_output.evidence_outputs"),
        )
        for name in ("semantic_metadata", "semantic_statistics", "semantic_trace_facts"):
            object.__setattr__(
                self,
                name,
                _freeze_pairs(getattr(self, name), f"execution_output.{name}"),
            )
        semantic_diagnostics = tuple((code, message) for code, message in self.semantic_diagnostics)
        object.__setattr__(self, "semantic_diagnostics", semantic_diagnostics)
        diagnostic_codes = tuple(code for code, _ in semantic_diagnostics)
        _require_strings(diagnostic_codes, "execution_output.semantic_diagnostics")
        if any(
            not isinstance(message, str) or not message.strip()
            for _, message in semantic_diagnostics
        ):
            raise DataIntegrityError("diagnostic messages must be non-empty")
        if self.outcome == "success" and not self.evidence_outputs:
            raise DataIntegrityError("success must contain declared evidence output")
        if self.outcome != "success" and self.evidence_outputs:
            raise DataIntegrityError("non-success outcomes cannot contain evidence output")
        if self.outcome == "valid_empty" and not self.semantic_diagnostics:
            raise DataIntegrityError("valid empty output must be explicit")
        if self.outcome in _FAILURE_OUTCOMES and not self.semantic_diagnostics:
            raise DataIntegrityError("producer failures require deterministic diagnostics")


@dataclass(frozen=True, slots=True)
class ProducerContract:
    """Blueprint v1.1 A02 producer contract governed by ADR-01 and ADR-02."""

    producer_identity: str
    owner: str
    producer_version: str
    contract_version: str
    implementation_identity: str
    capabilities: tuple[ProducerCapability, ...]
    configuration_schema_version: str
    configuration_fields: tuple[str, ...]
    configuration_compatibility: tuple[str, ...]
    input_schema_version: str
    output_schema_version: str
    diagnostic_schema_version: str
    failure_schema_version: str
    supported_timeframes: tuple[str, ...]
    execution_profile: str
    isolation_profile: str
    resource_profile: str
    execution_properties: tuple[str, ...]
    resource_requirements: tuple[str, ...]
    isolation_properties: tuple[str, ...]
    cancellation_properties: tuple[str, ...]
    concurrency_properties: tuple[str, ...]
    idempotency_classification: str
    determinism_profile: str
    replay_profile: str
    security_classification: str
    trust_classification: str
    failure_codes: tuple[str, ...]
    certification_requirements: tuple[str, ...]
    certification_evidence_references: tuple[str, ...] = ()
    replacement_metadata: tuple[str, ...] = ()
    deprecation_metadata: tuple[str, ...] = ()
    retirement_metadata: tuple[str, ...] = ()
    stateful: bool = False
    declared_side_effects: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        """Validate descriptor completeness without performing A03 admission."""

        object.__setattr__(self, "capabilities", tuple(self.capabilities))
        for name in (
            "configuration_fields",
            "configuration_compatibility",
            "supported_timeframes",
            "execution_properties",
            "resource_requirements",
            "isolation_properties",
            "cancellation_properties",
            "concurrency_properties",
            "failure_codes",
            "certification_requirements",
            "certification_evidence_references",
            "replacement_metadata",
            "deprecation_metadata",
            "retirement_metadata",
            "declared_side_effects",
        ):
            object.__setattr__(self, name, tuple(getattr(self, name)))
        _require_boolean(self.stateful, "producer_contract.stateful")
        _validate_producer_contract(self)

    def validate_input(self, execution_input: ProducerExecutionInput) -> None:
        """Validate an A02 manifest without resolving dependencies or planning."""

        _validate_input_contract(self, execution_input)

    def validate_environment(self, environment: ProducerExecutionEnvironment) -> None:
        """Validate granted A02 profiles without scheduling or dispatching."""

        if environment.execution_profile != self.execution_profile:
            raise DataIntegrityError("execution profile is not declared by producer contract")
        if environment.isolation_profile != self.isolation_profile:
            raise DataIntegrityError("isolation profile is not declared by producer contract")
        if environment.resource_profile != self.resource_profile:
            raise DataIntegrityError("resource profile is not declared by producer contract")
        if not set(environment.control_signals) <= set(self.cancellation_properties):
            raise DataIntegrityError(
                "execution control signal is not declared by producer contract"
            )

    def validate_output(
        self,
        execution_input: ProducerExecutionInput,
        output: ProducerExecutionOutput,
    ) -> None:
        """Validate candidate output without committing or publishing it."""

        _validate_output_contract(self, execution_input, output)


@runtime_checkable
class EvidenceProducer(Protocol):
    """Blueprint v1.1 A02 producer protocol governed by ADR-01 and ADR-02."""

    @property
    def producer_contract(self) -> ProducerContract:
        """Return the producer's immutable A02 contract."""

    def produce(
        self,
        execution_input: ProducerExecutionInput,
        environment: ProducerExecutionEnvironment,
    ) -> ProducerExecutionOutput:
        """Perform only the declared analytical transformation for one grant."""


def _validate_capability_contract(capability: ProducerCapability) -> None:
    for name in ("identity", "version", "category", "output_schema_version"):
        require_text(getattr(capability, name), f"capability.{name}")
    for name, required in (
        ("accepted_input_semantics", True),
        ("produced_output_semantics", True),
        ("required_dependencies", False),
        ("optional_dependencies", False),
        ("context_fields", False),
        ("temporal_requirements", False),
        ("compatibility_claims", False),
        ("certification_obligations", True),
    ):
        _require_strings(getattr(capability, name), f"capability.{name}", required=required)
    if set(capability.required_dependencies) & set(capability.optional_dependencies):
        raise DataIntegrityError("required and optional dependencies must be disjoint")


def _validate_producer_contract(contract: ProducerContract) -> None:
    for name in (
        "producer_identity",
        "owner",
        "producer_version",
        "contract_version",
        "implementation_identity",
        "configuration_schema_version",
        "input_schema_version",
        "output_schema_version",
        "diagnostic_schema_version",
        "failure_schema_version",
        "execution_profile",
        "isolation_profile",
        "resource_profile",
        "idempotency_classification",
        "determinism_profile",
        "replay_profile",
        "security_classification",
        "trust_classification",
    ):
        require_text(getattr(contract, name), f"producer_contract.{name}")
    if not contract.capabilities:
        raise DataIntegrityError("producer contract requires at least one capability")
    capability_keys = tuple(
        (capability.identity, capability.version) for capability in contract.capabilities
    )
    if len(set(capability_keys)) != len(capability_keys):
        raise DataIntegrityError("producer capability versions must be unique")
    optional_declarations = {
        "configuration_fields",
        "certification_evidence_references",
        "replacement_metadata",
        "deprecation_metadata",
        "retirement_metadata",
    }
    for name in (
        "configuration_fields",
        "configuration_compatibility",
        "supported_timeframes",
        "execution_properties",
        "resource_requirements",
        "isolation_properties",
        "cancellation_properties",
        "concurrency_properties",
        "failure_codes",
        "certification_requirements",
        "certification_evidence_references",
        "replacement_metadata",
        "deprecation_metadata",
        "retirement_metadata",
    ):
        _require_strings(
            getattr(contract, name),
            f"producer_contract.{name}",
            required=name not in optional_declarations,
        )
    if not _FAILURE_OUTCOMES <= set(contract.failure_codes):
        raise DataIntegrityError("producer failure vocabulary is incomplete")
    if contract.stateful:
        raise DataIntegrityError("cross-invocation producer state is prohibited")
    if contract.declared_side_effects:
        raise DataIntegrityError("producer side effects are prohibited")


def _selected_capabilities(
    contract: ProducerContract, selected: tuple[tuple[str, str], ...]
) -> tuple[ProducerCapability, ...]:
    by_identity = {
        (capability.identity, capability.version): capability
        for capability in contract.capabilities
    }
    try:
        return tuple(by_identity[reference] for reference in selected)
    except KeyError as error:
        raise DataIntegrityError("input selects an undeclared capability") from error


def _validate_input_contract(
    contract: ProducerContract, execution_input: ProducerExecutionInput
) -> None:
    if (
        execution_input.producer_identity,
        execution_input.producer_version,
        execution_input.contract_version,
    ) != (contract.producer_identity, contract.producer_version, contract.contract_version):
        raise DataIntegrityError("input producer contract reference does not match")
    selected = _selected_capabilities(contract, execution_input.selected_capabilities)
    if execution_input.configuration_schema_version != contract.configuration_schema_version:
        raise DataIntegrityError("configuration schema version does not match")
    if execution_input.input_schema_version != contract.input_schema_version:
        raise DataIntegrityError("input schema version does not match")
    configuration_names = {name for name, _ in execution_input.configuration}
    if configuration_names != set(contract.configuration_fields):
        raise DataIntegrityError("configuration projection does not match declared fields")
    required_context = {field for capability in selected for field in capability.context_fields}
    context_names = {name for name, _ in execution_input.context_projection}
    if context_names != required_context:
        raise DataIntegrityError("context projection does not match selected capabilities")
    required_dependencies = {
        dependency for capability in selected for dependency in capability.required_dependencies
    }
    optional_dependencies = {
        dependency for capability in selected for dependency in capability.optional_dependencies
    }
    dependency_names = {name for name, _ in execution_input.dependencies}
    _detect_undeclared_dependencies(
        dependency_names,
        required_dependencies,
        optional_dependencies,
    )
    if execution_input.timeframe not in contract.supported_timeframes:
        raise DataIntegrityError("timeframe is not declared by producer contract")


def _detect_undeclared_dependencies(
    actual: set[str], required: set[str], optional: set[str]
) -> None:
    if missing := required - actual:
        raise DataIntegrityError(f"required dependencies are missing: {sorted(missing)!r}")
    if undeclared := actual - required - optional:
        raise DataIntegrityError(f"undeclared dependencies are present: {sorted(undeclared)!r}")


def _validate_output_contract(
    contract: ProducerContract,
    execution_input: ProducerExecutionInput,
    output: ProducerExecutionOutput,
) -> None:
    if (
        output.producer_identity,
        output.producer_version,
        output.contract_version,
        output.input_manifest_reference,
    ) != (
        contract.producer_identity,
        contract.producer_version,
        contract.contract_version,
        execution_input.manifest_reference,
    ):
        raise DataIntegrityError("output provenance does not match producer invocation")
    if output.capability_references != execution_input.selected_capabilities:
        raise DataIntegrityError("output capability set does not match input grant")
    if (
        output.output_schema_version,
        output.diagnostic_schema_version,
        output.failure_schema_version,
    ) != (
        contract.output_schema_version,
        contract.diagnostic_schema_version,
        contract.failure_schema_version,
    ):
        raise DataIntegrityError("output schema versions do not match producer contract")
    selected = _selected_capabilities(contract, output.capability_references)
    declared_outputs = {
        semantic for capability in selected for semantic in capability.produced_output_semantics
    }
    output_semantics = {semantic for semantic, _ in output.evidence_outputs}
    if not output_semantics <= declared_outputs:
        raise DataIntegrityError("output contains undeclared evidence semantics")
    if output.outcome == "valid_empty" and not all(
        capability.valid_empty_supported for capability in selected
    ):
        raise DataIntegrityError("valid empty is not declared for every selected capability")


def _evaluate_producer_conformance(producer: object) -> bool:
    """Return structural A02 conformance without admission or certification."""

    if not isinstance(producer, EvidenceProducer) or not isinstance(
        producer.producer_contract, ProducerContract
    ):
        return False
    if producer.producer_contract.stateful or producer.producer_contract.declared_side_effects:
        return False
    try:
        instance_state = vars(producer)
    except TypeError:
        instance_state = {}
    if not set(instance_state) <= {"producer_contract"}:
        return False
    slot_state: set[str] = set()
    for owner in type(producer).__mro__:
        declared_slots = owner.__dict__.get("__slots__", ())
        if isinstance(declared_slots, str):
            declared_slots = (declared_slots,)
        slot_state.update(
            name
            for name in declared_slots
            if name not in {"__dict__", "__weakref__", "producer_contract"}
            and hasattr(producer, name)
        )
        for name, value in owner.__dict__.items():
            if (
                name == "producer_contract"
                or name.startswith("__")
                or callable(value)
                or isinstance(value, (property, staticmethod, classmethod))
            ):
                continue
            return False
    return not slot_state
