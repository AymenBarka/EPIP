from dataclasses import replace

import pytest

from epip.a07.direction import DirectionalFacts
from epip.a07.entry import EntryFacts
from epip.a07.evidence import StrategyEvidenceSnapshot
from epip.a07.foundation import StrategyDirection, StrategyEvidenceIdentity
from epip.a07.stop import StopFacts
from epip.a07.target import TargetFacts
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import (
    EvaluationContext,
    ProvenanceManifest,
    StrategyFactBundle,
    StrategyProfile,
)


def _bundle(
    context: EvaluationContext, profile: StrategyProfile, provenance: ProvenanceManifest
) -> StrategyFactBundle:
    evidence_identity = StrategyEvidenceIdentity("evidence", provenance.manifest_id)
    evidence = (
        StrategyEvidenceSnapshot(
            profile.strategy_identity, evidence_identity, "context", True, True
        ),
    )
    return StrategyFactBundle.create(
        evaluation_id=context.evaluation_id,
        strategy_identity=profile.strategy_identity,
        policy_reference="policy:1",
        profile_identity=profile.identity,
        evidence_identity=evidence_identity,
        evidence=evidence,
        directional_facts=DirectionalFacts(*((StrategyDirection.BUY,) * 6)),
        entry_facts=EntryFacts(100.0, 100.0),
        stop_facts=StopFacts(95.0),
        target_facts=TargetFacts(115.0),
        confidence=0.75,
        mtf_context_id="mtf:1",
        provenance=provenance,
    )


def test_fact_bundle_reuses_frozen_a07_facts(
    context: EvaluationContext, profile: StrategyProfile, provenance: ProvenanceManifest
) -> None:
    bundle = _bundle(context, profile, provenance)
    assert bundle.confidence == 0.75
    assert hash(bundle)
    with pytest.raises(DataIntegrityError):
        replace(bundle, confidence=float("nan"))


def test_fact_bundle_rejects_incomplete_provenance(
    context: EvaluationContext, profile: StrategyProfile, provenance: ProvenanceManifest
) -> None:
    incomplete = ProvenanceManifest.create(
        provenance.sources,
        provenance.facts[:-1],
        provenance.profile_identity,
        provenance.adapter_identity,
        provenance.evaluation_id,
    )
    with pytest.raises(DataIntegrityError):
        _bundle(context, profile, incomplete)
