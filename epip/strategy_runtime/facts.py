"""Typed analytical input and A07 fact-bundle contracts."""

from __future__ import annotations

from dataclasses import dataclass

from epip.a07.direction import DirectionalFacts
from epip.a07.entry import EntryFacts
from epip.a07.evidence import StrategyEvidenceSnapshot
from epip.a07.foundation import StrategyEvidenceIdentity, StrategyIdentity
from epip.a07.stop import StopFacts
from epip.a07.target import TargetFacts
from epip.context import MarketContextSnapshot
from epip.core import KernelResult
from epip.core.integrity import DataIntegrityError
from epip.decision import DecisionSnapshot
from epip.elliott import WaveSnapshot
from epip.fibonacci import FibonacciSnapshot
from epip.liquidity import LiquiditySnapshot
from epip.market_structure import MarketStructureSnapshot
from epip.strategy_runtime._base import CONTRACT_VERSION, digest, finite, text
from epip.strategy_runtime.mtf import MultiTimeframeInputSet
from epip.strategy_runtime.profile import StrategyProfileIdentity
from epip.strategy_runtime.provenance import ProvenanceManifest
from epip.swing import SwingSequence


@dataclass(frozen=True, slots=True)
class AnalyticalInputBundle:
    swing: SwingSequence | None
    structure: MarketStructureSnapshot | None
    liquidity: LiquiditySnapshot | None
    fibonacci: FibonacciSnapshot | None
    context: MarketContextSnapshot | None
    elliott: WaveSnapshot | None
    decision: DecisionSnapshot | None
    kernel_result: KernelResult | None
    mtf_context: MultiTimeframeInputSet
    provenance: ProvenanceManifest

    def __post_init__(self) -> None:
        if type(self.mtf_context) is not MultiTimeframeInputSet:
            raise DataIntegrityError("mtf_context must be a MultiTimeframeInputSet")
        if type(self.provenance) is not ProvenanceManifest:
            raise DataIntegrityError("provenance must be a ProvenanceManifest")
        symbol_timeframes: set[tuple[str, str]] = set()
        for item in (
            self.structure,
            self.liquidity,
            self.fibonacci,
            self.context,
            self.elliott,
            self.decision,
        ):
            if item is not None and hasattr(item, "symbol") and hasattr(item, "timeframe"):
                symbol_timeframes.add((item.symbol, item.timeframe))
        if len(symbol_timeframes) > 1:
            raise DataIntegrityError("analytical snapshots must be symbol/timeframe coherent")


_FACT_KEYS = frozenset(
    {
        "direction.elliott",
        "direction.trend",
        "direction.structure",
        "direction.mtf",
        "direction.primary",
        "direction.alternate",
        "entry",
        "stop",
        "target",
        "confidence",
        "evidence",
    }
)


@dataclass(frozen=True, slots=True)
class StrategyFactBundle:
    contract_version: str
    bundle_id: str
    evaluation_id: str
    strategy_identity: StrategyIdentity
    policy_reference: str
    profile_identity: StrategyProfileIdentity
    evidence_identity: StrategyEvidenceIdentity
    evidence: tuple[StrategyEvidenceSnapshot, ...]
    directional_facts: DirectionalFacts
    entry_facts: EntryFacts
    stop_facts: StopFacts
    target_facts: TargetFacts
    confidence: float
    mtf_context_id: str
    provenance: ProvenanceManifest

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported fact-bundle contract version")
        for name in ("evaluation_id", "policy_reference", "mtf_context_id"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        expected_types = (
            (self.strategy_identity, StrategyIdentity, "strategy_identity"),
            (self.profile_identity, StrategyProfileIdentity, "profile_identity"),
            (self.evidence_identity, StrategyEvidenceIdentity, "evidence_identity"),
            (self.directional_facts, DirectionalFacts, "directional_facts"),
            (self.entry_facts, EntryFacts, "entry_facts"),
            (self.stop_facts, StopFacts, "stop_facts"),
            (self.target_facts, TargetFacts, "target_facts"),
            (self.provenance, ProvenanceManifest, "provenance"),
        )
        for value, expected, name in expected_types:
            if type(value) is not expected:
                raise DataIntegrityError(f"{name} has the wrong contract type")
        if type(self.evidence) is not tuple or not self.evidence:
            raise DataIntegrityError("evidence must be a non-empty tuple")
        if any(type(item) is not StrategyEvidenceSnapshot for item in self.evidence):
            raise DataIntegrityError("evidence contains an invalid contract")
        if any(item.strategy_identity != self.strategy_identity for item in self.evidence):
            raise DataIntegrityError("evidence strategy identity mismatch")
        if len({item.evidence_key for item in self.evidence}) != len(self.evidence):
            raise DataIntegrityError("evidence keys must be unique")
        if len({item.evidence_identity for item in self.evidence}) != len(self.evidence):
            raise DataIntegrityError("evidence item identities must be unique")
        confidence = finite(self.confidence, "confidence")
        if not 0.0 <= confidence <= 1.0:
            raise DataIntegrityError("confidence must be within [0, 1]")
        object.__setattr__(self, "confidence", confidence)
        if self.evaluation_id != self.provenance.evaluation_id:
            raise DataIntegrityError("bundle and provenance evaluation identities differ")
        if self.profile_identity != self.provenance.profile_identity:
            raise DataIntegrityError("bundle and provenance profiles differ")
        keys = {item.fact_key for item in self.provenance.facts}
        if not _FACT_KEYS <= keys:
            raise DataIntegrityError("required per-fact provenance is incomplete")
        expected_id = digest(self, exclude=frozenset({"bundle_id"}))
        if self.bundle_id != expected_id:
            raise DataIntegrityError("bundle_id does not match canonical facts")

    @classmethod
    def create(
        cls,
        *,
        evaluation_id: str,
        strategy_identity: StrategyIdentity,
        policy_reference: str,
        profile_identity: StrategyProfileIdentity,
        evidence_identity: StrategyEvidenceIdentity,
        evidence: tuple[StrategyEvidenceSnapshot, ...],
        directional_facts: DirectionalFacts,
        entry_facts: EntryFacts,
        stop_facts: StopFacts,
        target_facts: TargetFacts,
        confidence: float,
        mtf_context_id: str,
        provenance: ProvenanceManifest,
    ) -> StrategyFactBundle:
        values = {
            "evaluation_id": evaluation_id,
            "strategy_identity": strategy_identity,
            "policy_reference": policy_reference,
            "profile_identity": profile_identity,
            "evidence_identity": evidence_identity,
            "evidence": evidence,
            "directional_facts": directional_facts,
            "entry_facts": entry_facts,
            "stop_facts": stop_facts,
            "target_facts": target_facts,
            "confidence": confidence,
            "mtf_context_id": mtf_context_id,
            "provenance": provenance,
        }
        candidate = object.__new__(cls)
        object.__setattr__(candidate, "contract_version", CONTRACT_VERSION)
        object.__setattr__(candidate, "bundle_id", "")
        for name, value in values.items():
            object.__setattr__(candidate, name, value)
        return cls(
            CONTRACT_VERSION,
            digest(candidate, exclude=frozenset({"bundle_id"})),
            evaluation_id,
            strategy_identity,
            policy_reference,
            profile_identity,
            evidence_identity,
            evidence,
            directional_facts,
            entry_facts,
            stop_facts,
            target_facts,
            confidence,
            mtf_context_id,
            provenance,
        )
