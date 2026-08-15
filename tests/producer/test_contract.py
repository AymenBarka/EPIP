"""Programme A Blueprint v1.1 A02 tests governed by ADR-01 and ADR-02."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from typing import ClassVar

import pytest

from epip.core.integrity import DataIntegrityError
from epip.producer import (
    EvidenceProducer,
    ProducerCapability,
    ProducerContract,
    ProducerExecutionEnvironment,
    ProducerExecutionInput,
    ProducerExecutionOutput,
)
from epip.producer.contract import _evaluate_producer_conformance


def _capability(**overrides: object) -> ProducerCapability:
    values: dict[str, object] = {
        "identity": "market.structure",
        "version": "1.0.0",
        "category": "analytical",
        "accepted_input_semantics": ("price.series",),
        "produced_output_semantics": ("market.structure",),
        "required_dependencies": ("swing.structure",),
        "optional_dependencies": ("session.context",),
        "context_fields": ("symbol", "session"),
        "temporal_requirements": ("closed_boundary",),
        "output_schema_version": "1",
        "valid_empty_supported": True,
        "compatibility_claims": (),
        "certification_obligations": ("determinism", "isolation"),
    }
    values.update(overrides)
    return ProducerCapability(**values)  # type: ignore[arg-type]


def _contract(**overrides: object) -> ProducerContract:
    values: dict[str, object] = {
        "producer_identity": "producer.market-structure",
        "owner": "market-structure-domain",
        "producer_version": "1.0.0",
        "contract_version": "1.0.0",
        "implementation_identity": "build-001",
        "capabilities": (_capability(),),
        "configuration_schema_version": "1",
        "configuration_fields": ("lookback",),
        "configuration_compatibility": ("exact",),
        "input_schema_version": "1",
        "output_schema_version": "1",
        "diagnostic_schema_version": "1",
        "failure_schema_version": "1",
        "supported_timeframes": ("H1",),
        "execution_profile": "bounded",
        "isolation_profile": "invocation-local",
        "resource_profile": "declared",
        "execution_properties": ("single-terminal-submission",),
        "resource_requirements": ("bounded",),
        "isolation_properties": ("no-shared-state",),
        "cancellation_properties": ("cooperative-cancellation",),
        "concurrency_properties": ("not-shared",),
        "idempotency_classification": "idempotent",
        "determinism_profile": "output-deterministic",
        "replay_profile": "historical-input",
        "security_classification": "least-privilege",
        "trust_classification": "approved-boundary",
        "failure_codes": (
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
        ),
        "certification_requirements": ("real-execution",),
    }
    values.update(overrides)
    return ProducerContract(**values)  # type: ignore[arg-type]


def _execution_input(**overrides: object) -> ProducerExecutionInput:
    values: dict[str, object] = {
        "manifest_reference": "manifest-001",
        "producer_identity": "producer.market-structure",
        "producer_version": "1.0.0",
        "contract_version": "1.0.0",
        "selected_capabilities": (("market.structure", "1.0.0"),),
        "input_schema_version": "1",
        "configuration_schema_version": "1",
        "configuration": (("lookback", 20),),
        "context_schema_version": "1",
        "context_source_authority": "control-plane",
        "context_projection": (("symbol", "EURUSD"), ("session", "london")),
        "dependencies": (("swing.structure", ("swing-1",)),),
        "symbol": "EURUSD",
        "timeframe": "H1",
        "temporal_boundary": "2026-08-14T10:00:00Z",
        "data_revision": "revision-1",
        "registry_snapshot_reference": "registry-1",
        "semantic_plan_reference": "plan-1",
    }
    values.update(overrides)
    return ProducerExecutionInput(**values)  # type: ignore[arg-type]


def _output(**overrides: object) -> ProducerExecutionOutput:
    values: dict[str, object] = {
        "input_manifest_reference": "manifest-001",
        "producer_identity": "producer.market-structure",
        "producer_version": "1.0.0",
        "contract_version": "1.0.0",
        "capability_references": (("market.structure", "1.0.0"),),
        "output_schema_version": "1",
        "diagnostic_schema_version": "1",
        "failure_schema_version": "1",
        "outcome": "success",
        "evidence_outputs": (("market.structure", ("bullish",)),),
        "semantic_metadata": (("method", "declared"),),
        "semantic_diagnostics": (),
        "semantic_statistics": (("observations", 1),),
        "semantic_trace_facts": (("rule", "structure-break"),),
    }
    values.update(overrides)
    return ProducerExecutionOutput(**values)  # type: ignore[arg-type]


def test_public_artifacts_are_exactly_the_a02_blueprint_inventory() -> None:
    from epip import producer

    assert set(producer.__all__) == {
        "EvidenceProducer",
        "ProducerCapability",
        "ProducerContract",
        "ProducerExecutionEnvironment",
        "ProducerExecutionInput",
        "ProducerExecutionOutput",
    }


def test_contract_and_envelopes_are_immutable_and_validate_together() -> None:
    contract = _contract()
    execution_input = _execution_input()
    environment = ProducerExecutionEnvironment(
        execution_profile="bounded",
        isolation_profile="invocation-local",
        resource_profile="declared",
        cancellation_requested=False,
    )
    output = _output()

    contract.validate_input(execution_input)
    contract.validate_environment(environment)
    contract.validate_output(execution_input, output)

    with pytest.raises(FrozenInstanceError):
        contract.owner = "other"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        execution_input.symbol = "GBPUSD"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        output.outcome = "valid_empty"  # type: ignore[misc]


def test_nested_input_and_output_values_are_deeply_frozen() -> None:
    mutable_configuration = {"windows": [5, 10]}
    execution_input = _execution_input(configuration=(("lookback", mutable_configuration),))
    mutable_configuration["windows"].append(20)
    assert execution_input.configuration[0][1] != mutable_configuration

    mutable_evidence = {"levels": [1.1, 1.2]}
    output = _output(evidence_outputs=(("market.structure", mutable_evidence),))
    mutable_evidence["levels"].append(1.3)
    assert output.evidence_outputs[0][1] != mutable_evidence


def test_all_accepted_container_fields_are_canonicalized_to_immutable_tuples() -> None:
    mutable_context_fields = ["symbol", "session"]
    capability = _capability(context_fields=mutable_context_fields)
    mutable_context_fields.append("mutable")
    assert capability.context_fields == ("symbol", "session")

    mutable_capabilities = [capability]
    contract = _contract(capabilities=mutable_capabilities)
    mutable_capabilities.clear()
    assert contract.capabilities == (capability,)

    mutable_selection = [["market.structure", "1.0.0"]]
    execution_input = _execution_input(selected_capabilities=mutable_selection)
    mutable_selection[0].append("mutable")
    assert execution_input.selected_capabilities == (("market.structure", "1.0.0"),)

    mutable_diagnostics = [["CODE", "message"]]
    output = _output(semantic_diagnostics=mutable_diagnostics)
    mutable_diagnostics[0].append("mutable")
    assert output.semantic_diagnostics == (("CODE", "message"),)


@pytest.mark.parametrize(
    "overrides",
    (
        {"identity": ""},
        {"accepted_input_semantics": ()},
        {"produced_output_semantics": ()},
        {"required_dependencies": ("same",), "optional_dependencies": ("same",)},
        {"certification_obligations": ()},
        {"valid_empty_supported": 1},
        {"atomic_semantic_group": "false"},
    ),
)
def test_capability_declarations_fail_closed(overrides: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, ValueError)):
        _capability(**overrides)


@pytest.mark.parametrize(
    "overrides",
    (
        {"capabilities": ()},
        {"stateful": True},
        {"declared_side_effects": ("network-write",)},
        {"certification_requirements": ()},
        {"supported_timeframes": ()},
        {"stateful": ""},
    ),
)
def test_producer_contracts_fail_closed(overrides: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, ValueError)):
        _contract(**overrides)


@pytest.mark.parametrize(
    "overrides",
    (
        {"producer_identity": "other"},
        {"selected_capabilities": (("undeclared", "1.0.0"),)},
        {"configuration_schema_version": "2"},
        {"configuration": ()},
        {"context_projection": (("symbol", "EURUSD"),)},
        {"dependencies": ()},
        {"dependencies": (("hidden", "value"), ("swing.structure", "value"))},
        {"timeframe": "M1"},
    ),
)
def test_input_visibility_fails_closed(overrides: dict[str, object]) -> None:
    contract = _contract()
    with pytest.raises((DataIntegrityError, ValueError)):
        contract.validate_input(_execution_input(**overrides))


@pytest.mark.parametrize(
    "overrides",
    (
        {"execution_profile": "other"},
        {"isolation_profile": "other"},
        {"resource_profile": "other"},
    ),
)
def test_execution_environment_fails_closed(overrides: dict[str, object]) -> None:
    environment_values: dict[str, object] = {
        "execution_profile": "bounded",
        "isolation_profile": "invocation-local",
        "resource_profile": "declared",
        "cancellation_requested": False,
    }
    environment_values.update(overrides)
    environment = ProducerExecutionEnvironment(**environment_values)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        _contract().validate_environment(environment)


def test_execution_environment_requires_a_strict_cancellation_boolean() -> None:
    with pytest.raises(DataIntegrityError):
        ProducerExecutionEnvironment(
            execution_profile="bounded",
            isolation_profile="invocation-local",
            resource_profile="declared",
            cancellation_requested=0,  # type: ignore[arg-type]
        )


@pytest.mark.parametrize(
    "overrides",
    (
        {"input_manifest_reference": "other"},
        {"producer_version": "2.0.0"},
        {"capability_references": (("other", "1.0.0"),)},
        {"evidence_outputs": (("undeclared", "value"),)},
    ),
)
def test_output_contract_fails_closed(overrides: dict[str, object]) -> None:
    with pytest.raises((DataIntegrityError, ValueError)):
        _contract().validate_output(_execution_input(), _output(**overrides))


def test_valid_empty_is_explicit_and_distinct_from_failure() -> None:
    valid_empty = _output(
        outcome="valid_empty",
        evidence_outputs=(),
        semantic_diagnostics=(("NO_EVIDENCE", "No evidence for the granted boundary"),),
    )
    failure = _output(
        outcome="dependency_unavailable",
        evidence_outputs=(),
        semantic_diagnostics=(("DEPENDENCY_UNAVAILABLE", "Required dependency unavailable"),),
    )
    contract = _contract()
    contract.validate_output(_execution_input(), valid_empty)
    contract.validate_output(_execution_input(), failure)
    assert valid_empty.outcome != failure.outcome


def test_partial_evidence_cannot_be_submitted_as_failure() -> None:
    with pytest.raises(DataIntegrityError):
        _output(
            outcome="analytical_execution_failure",
            evidence_outputs=(("market.structure", "partial"),),
            semantic_diagnostics=(("ANALYTICAL_FAILURE", "Analysis failed"),),
        )


def test_ambient_and_mutable_state_fail_closed() -> None:
    with pytest.raises(DataIntegrityError):
        _execution_input(context_projection=(("symbol", object()), ("session", "london")))


def test_evidence_producer_protocol_is_structural_without_execution() -> None:
    class ConformingProducer:
        producer_contract = _contract()

        def produce(
            self,
            execution_input: ProducerExecutionInput,
            environment: ProducerExecutionEnvironment,
        ) -> ProducerExecutionOutput:
            self.producer_contract.validate_input(execution_input)
            self.producer_contract.validate_environment(environment)
            return _output()

    producer = ConformingProducer()
    assert isinstance(producer, EvidenceProducer)
    assert _evaluate_producer_conformance(producer)


def test_conformance_rejects_cross_invocation_instance_state() -> None:
    class StatefulProducer:
        producer_contract = _contract()

        def __init__(self) -> None:
            self.retained_results: list[ProducerExecutionOutput] = []

        def produce(
            self,
            execution_input: ProducerExecutionInput,
            environment: ProducerExecutionEnvironment,
        ) -> ProducerExecutionOutput:
            return _output()

    class SlottedStatefulProducer:
        __slots__ = ("retained_result",)
        producer_contract = _contract()

        def __init__(self) -> None:
            self.retained_result: ProducerExecutionOutput | None = None

        def produce(
            self,
            execution_input: ProducerExecutionInput,
            environment: ProducerExecutionEnvironment,
        ) -> ProducerExecutionOutput:
            return _output()

    class ClassStatefulProducer:
        producer_contract = _contract()
        retained_results: ClassVar[list[ProducerExecutionOutput]] = []

        def produce(
            self,
            execution_input: ProducerExecutionInput,
            environment: ProducerExecutionEnvironment,
        ) -> ProducerExecutionOutput:
            return _output()

    assert not _evaluate_producer_conformance(StatefulProducer())
    assert not _evaluate_producer_conformance(SlottedStatefulProducer())
    assert not _evaluate_producer_conformance(ClassStatefulProducer())


def test_no_downstream_authority_or_composite_artifact_is_exported() -> None:
    from epip import producer

    prohibited = {
        "ProducerRegistry",
        "RegistrySnapshot",
        "SemanticPlan",
        "DispatchPlan",
        "ExecutionAttempt",
        "DurableResultStore",
        "EvidenceCache",
        "ReplaySession",
        "ExecutionCheckpoint",
        "RecoveryRequest",
        "TerminalEvidenceSet",
    }
    assert prohibited.isdisjoint(producer.__all__)
