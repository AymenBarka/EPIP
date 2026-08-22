"""Deterministic provider execution for A04-E07."""

from __future__ import annotations

from typing import NamedTuple

from epip.core.integrity import DataIntegrityError
from epip.evidence.model import DiagnosticCode, DiagnosticReason, ResolutionProfile
from epip.evidence.orchestration import ExecutionSchedule
from epip.governance import GovernanceEpoch, RegistrySnapshot
from epip.producer import (
    EvidenceProducer,
    ProducerExecutionEnvironment,
    ProducerExecutionInput,
    ProducerExecutionOutput,
)

_ExecutionKey = tuple[str, str]
_ExecutionOutcome = tuple[str, str, ProducerExecutionOutput]


class ExecutionDiagnostics(NamedTuple):
    """Immutable diagnostics preserving the complete execution context."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    execution_schedule: ExecutionSchedule
    execution_layers: tuple[tuple[_ExecutionKey, ...], ...]
    executed_provider_identities: tuple[str, ...]
    execution_ordering: tuple[_ExecutionKey, ...]
    execution_barriers: tuple[tuple[int, tuple[_ExecutionKey, ...]], ...]
    outcomes: tuple[_ExecutionOutcome, ...]
    reasons: tuple[DiagnosticReason, ...]


class ExecutionResult(NamedTuple):
    """Immutable deterministic result of one authorized execution schedule."""

    snapshot_identity: str
    manifest_reference: str
    governance_epoch: GovernanceEpoch
    resolution_profile: ResolutionProfile
    execution_schedule: ExecutionSchedule
    execution_ordering: tuple[_ExecutionKey, ...]
    execution_barriers: tuple[tuple[int, tuple[_ExecutionKey, ...]], ...]
    outcomes: tuple[_ExecutionOutcome, ...]
    diagnostics: ExecutionDiagnostics


class ProviderExecutor:
    """Invoke authoritative ADR-02 producers in the frozen schedule order."""

    __slots__ = ()

    @classmethod
    def execute(
        cls,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
        bindings: tuple[tuple[str, EvidenceProducer], ...],
        execution_inputs: tuple[tuple[_ExecutionKey, ProducerExecutionInput], ...],
        environments: tuple[tuple[_ExecutionKey, ProducerExecutionEnvironment], ...],
    ) -> ExecutionResult:
        if not isinstance(schedule, ExecutionSchedule):
            raise DataIntegrityError("schedule must be immutable ExecutionSchedule")
        if not isinstance(snapshot, RegistrySnapshot):
            raise DataIntegrityError("snapshot must be immutable RegistrySnapshot")
        if not isinstance(profile, ResolutionProfile):
            raise DataIntegrityError("profile must be immutable ResolutionProfile")
        for value, name in (
            (bindings, "bindings"),
            (execution_inputs, "execution_inputs"),
            (environments, "environments"),
        ):
            if not isinstance(value, tuple):
                raise DataIntegrityError(f"{name} must be an immutable tuple")

        reason = cls._validate(
            schedule, snapshot, profile, bindings, execution_inputs, environments
        )
        outcomes: list[_ExecutionOutcome] = []
        executed: list[str] = []
        if reason is None:
            providers = dict(bindings)
            inputs = dict(execution_inputs)
            granted_environments = dict(environments)
            for layer in schedule.execution_layers:
                for requirement, identity in layer:
                    provider = providers[identity]
                    execution_input = inputs[(requirement, identity)]
                    try:
                        output = provider.produce(
                            execution_input,
                            granted_environments[(requirement, identity)],
                        )
                        if not isinstance(output, ProducerExecutionOutput):
                            raise DataIntegrityError(
                                "provider returned an invalid execution output"
                            )
                        provider.producer_contract.validate_output(execution_input, output)
                    except Exception as error:  # noqa: BLE001 - producer trust boundary
                        reason = cls._reason(
                            requirement,
                            identity,
                            f"provider execution failed: {type(error).__name__}",
                        )
                        break
                    outcomes.append((requirement, identity, output))
                    executed.append(identity)
                    if output.outcome not in {"success", "valid_empty"}:
                        reason = cls._reason(
                            requirement, identity, "provider reported a failure outcome"
                        )
                        break
                if reason is not None:
                    break

        ordering = schedule.scheduled_executions if reason is None else ()
        barriers = schedule.execution_barriers if reason is None else ()
        reasons = schedule.diagnostics.reasons
        if reason is not None:
            reasons = (*reasons, reason)
        immutable_outcomes = tuple(outcomes)
        diagnostics = ExecutionDiagnostics(
            schedule.snapshot_identity,
            schedule.manifest_reference,
            schedule.governance_epoch,
            schedule,
            schedule.execution_layers,
            tuple(executed),
            ordering,
            barriers,
            immutable_outcomes,
            reasons,
        )
        return ExecutionResult(
            schedule.snapshot_identity,
            schedule.manifest_reference,
            schedule.governance_epoch,
            profile,
            schedule,
            ordering,
            barriers,
            immutable_outcomes,
            diagnostics,
        )

    @classmethod
    def _validate(
        cls,
        schedule: ExecutionSchedule,
        snapshot: RegistrySnapshot,
        profile: ResolutionProfile,
        bindings: tuple[tuple[str, EvidenceProducer], ...],
        execution_inputs: tuple[tuple[_ExecutionKey, ProducerExecutionInput], ...],
        environments: tuple[tuple[_ExecutionKey, ProducerExecutionEnvironment], ...],
    ) -> DiagnosticReason | None:
        if (
            schedule.snapshot_identity != snapshot.snapshot_identity
            or schedule.manifest_reference != snapshot.manifest_reference
            or schedule.governance_epoch != snapshot.governance_epoch
            or schedule.resolution_profile != profile
            or schedule.scheduled_executions
            != tuple(item for layer in schedule.execution_layers for item in layer)
            or schedule.execution_barriers
            != tuple((index, layer) for index, layer in enumerate(schedule.execution_layers))
            or schedule.diagnostics.execution_schedule != schedule.execution_barriers
        ):
            return cls._reason("execution", None, "execution schedule is inconsistent")
        scheduled_identities = tuple(identity for _, identity in schedule.scheduled_executions)
        binding_identities = tuple(identity for identity, _ in bindings)
        if len(set(binding_identities)) != len(binding_identities):
            return cls._reason("execution", None, "provider binding is duplicated")
        if set(binding_identities) != set(scheduled_identities):
            return cls._reason("execution", None, "provider binding is missing or unauthorized")
        scheduled_keys = set(schedule.scheduled_executions)
        input_keys = tuple(key for key, _ in execution_inputs)
        environment_keys = tuple(key for key, _ in environments)
        if (
            len(set(input_keys)) != len(input_keys)
            or len(set(environment_keys)) != len(environment_keys)
            or set(input_keys) != scheduled_keys
            or set(environment_keys) != scheduled_keys
        ):
            return cls._reason("execution", None, "execution grants are incomplete")

        entries = {
            f"{entry.producer_identity}@{entry.producer_version}": entry
            for entry in snapshot.entries
        }
        inputs = dict(execution_inputs)
        granted_environments = dict(environments)
        for identity, provider in bindings:
            if not isinstance(provider, EvidenceProducer) or identity not in entries:
                return cls._reason("execution", identity, "provider binding is unauthorized")
            contract = provider.producer_contract
            entry = entries[identity]
            if (
                contract.producer_identity != entry.producer_identity
                or contract.producer_version != entry.producer_version
                or contract.contract_version != entry.producer_contract_version
                or contract.implementation_identity != entry.implementation_identity
            ):
                return cls._reason("execution", identity, "provider binding is inconsistent")
        try:
            for key in schedule.scheduled_executions:
                execution_input = inputs[key]
                environment = granted_environments[key]
                identity = key[1]
                provider = dict(bindings)[identity]
                if (
                    execution_input.producer_identity
                    != provider.producer_contract.producer_identity
                    or execution_input.producer_version
                    != provider.producer_contract.producer_version
                    or execution_input.manifest_reference != schedule.manifest_reference
                    or execution_input.registry_snapshot_reference != snapshot.snapshot_identity
                    or environment.cancellation_requested
                ):
                    return cls._reason(key[0], identity, "execution grant is inconsistent")
                provider.producer_contract.validate_input(execution_input)
                provider.producer_contract.validate_environment(environment)
        except (DataIntegrityError, AttributeError, TypeError):
            return cls._reason("execution", None, "execution grant validation failed")
        return None

    @staticmethod
    def _reason(requirement: str, candidate: str | None, reason: str) -> DiagnosticReason:
        return DiagnosticReason(DiagnosticCode.INVALID_DEPENDENCY, requirement, reason, candidate)
