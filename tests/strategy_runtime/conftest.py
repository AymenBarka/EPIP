from __future__ import annotations

import pytest

from epip.a07.confidence import ConfidenceValidation, SignalExpiration, StrategyConfidence
from epip.a07.direction import DirectionalDecision, DirectionalFacts, DirectionValidation
from epip.a07.entry import EntryFacts, EntryPrice, EntryValidation
from epip.a07.evidence import EvidenceBinding, EvidenceValidation, StrategyEvidenceSnapshot
from epip.a07.foundation import (
    StrategyDirection,
    StrategyEvaluationRequest,
    StrategyEvidenceIdentity,
    StrategyIdentity,
)
from epip.a07.policy import StrategyPolicy
from epip.a07.reward_risk import RewardRiskOutcome, RewardRiskValidation
from epip.a07.signal import StrategySignal
from epip.a07.stop import StopFacts, StopLoss, StopValidation
from epip.a07.target import TakeProfit, TargetFacts, TargetValidation
from epip.strategy_runtime import (
    EvaluationContext,
    FactAdapterIdentity,
    FactProvenance,
    MultiTimeframeInputSet,
    ProvenanceManifest,
    RuntimeMode,
    SourceProvenance,
    StrategyProfile,
    TimeframeInput,
    TimeframeRole,
)


@pytest.fixture
def strategy_identity() -> StrategyIdentity:
    return StrategyIdentity("profile", "1")


@pytest.fixture
def profile(strategy_identity: StrategyIdentity) -> StrategyProfile:
    return StrategyProfile.create(
        profile_id="profile",
        profile_version="1",
        strategy_identity=strategy_identity,
        compatible_runtime_contract_versions=("p01-v1",),
        compatible_adapter_contract_versions=("p01-v1",),
        required_source_domains=("context",),
        optional_source_domains=("elliott",),
        required_evidence_keys=("context",),
        optional_evidence_keys=("elliott",),
        enabled_direction_facts=("alternate", "elliott", "mtf", "primary", "structure", "trend"),
        enabled_geometry_sources=("entry", "stop", "target"),
        confidence_model_reference="confidence:1",
        evidence_taxonomy_reference="evidence:1",
        mtf_requirement="primary-closed:1",
        mapping_rules_reference="mapping:1",
    )


@pytest.fixture
def context(profile: StrategyProfile) -> EvaluationContext:
    return EvaluationContext.create(
        instrument_id="instrument:EURUSD",
        symbol="EURUSD",
        primary_timeframe="H1",
        evaluation_timestamp="2026-08-24T12:30:15.123456Z",
        event_timestamp="2026-08-24T12:30:15.123456Z",
        receipt_timestamp="2026-08-24T12:30:16Z",
        runtime_mode=RuntimeMode.PAPER,
        profile_identity=profile.identity,
        source_set_id="sources:1",
        run_id="run:1",
    )


@pytest.fixture
def adapter_identity() -> FactAdapterIdentity:
    return FactAdapterIdentity("adapter", "1", "p01-v1", "a" * 64)


@pytest.fixture
def mtf() -> MultiTimeframeInputSet:
    frame = TimeframeInput(
        "H1",
        TimeframeRole.PRIMARY,
        "2026-08-24T11:00:00Z",
        "2026-08-24T12:00:00Z",
        "2026-08-24T12:00:00Z",
        True,
        ("context-1",),
        ("source-1",),
    )
    return MultiTimeframeInputSet.create("H1", "2026-08-24T12:30:15.123456Z", (frame,))


@pytest.fixture
def provenance(
    context: EvaluationContext,
    profile: StrategyProfile,
    adapter_identity: FactAdapterIdentity,
) -> ProvenanceManifest:
    source = SourceProvenance(
        "context",
        "MarketContextSnapshot",
        "EPIP-010",
        "source-1",
        context.event_timestamp,
        "EPIP-010",
        "feed-1",
        "b" * 64,
    )
    keys = (
        "confidence",
        "direction.alternate",
        "direction.elliott",
        "direction.mtf",
        "direction.primary",
        "direction.structure",
        "direction.trend",
        "entry",
        "evidence",
        "stop",
        "target",
    )
    facts = tuple(
        FactProvenance(
            key,
            ("source-1",),
            "adapter",
            "1",
            "profile",
            "1",
            f"map-{key}",
            "1",
            "c" * 64,
        )
        for key in keys
    )
    return ProvenanceManifest.create(
        (source,), facts, profile.identity, adapter_identity, context.evaluation_id
    )


@pytest.fixture
def signal(strategy_identity: StrategyIdentity) -> StrategySignal:
    evidence_identity = StrategyEvidenceIdentity("evidence", "manifest")
    policy = StrategyPolicy(
        "policy",
        "1",
        strategy_identity,
        (StrategyDirection.BUY, StrategyDirection.SELL),
        2.0,
        0.5,
        ("context",),
        (),
        90,
        6,
        (),
    )
    available = (
        StrategyEvidenceSnapshot(strategy_identity, evidence_identity, "context", True, True),
    )
    evidence = EvidenceValidation(EvidenceBinding(policy, available))
    directions = DirectionalFacts(*((StrategyDirection.BUY,) * 6))
    direction = DirectionValidation(DirectionalDecision(policy, evidence, directions))
    entry = EntryValidation(EntryPrice(direction, EntryFacts(100.0, 100.0)))
    reward_risk = RewardRiskValidation(
        RewardRiskOutcome(
            entry,
            StopValidation(StopLoss(entry, StopFacts(95.0))),
            TargetValidation(TakeProfit(entry, TargetFacts(115.0))),
        )
    )
    confidence = StrategyConfidence(evidence, direction, reward_risk, 0.75)
    request = StrategyEvaluationRequest(
        strategy_identity,
        evidence_identity,
        "2026-08-24T12:30:15.123456Z",
        "baseline",
        policy.identity.reference,
    )
    return StrategySignal(ConfidenceValidation(confidence, SignalExpiration(request, confidence)))
