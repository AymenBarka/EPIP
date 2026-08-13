"""Deterministic structural inference for the EPIP-016 decision domain.

Inference interprets registered evidence as hypotheses and groups compatible
hypotheses into scenarios.  It deliberately performs no ranking, selection,
risk evaluation, recommendation, or financial calculation.
"""

from __future__ import annotations

import hashlib
import json
from collections.abc import Iterator, Mapping
from dataclasses import dataclass
from enum import StrEnum
from types import MappingProxyType

from epip.core.integrity import RelationshipIntegrityError, require_text, require_version
from epip.decision.domain import (
    Confidence,
    ConfidenceLevel,
    DecisionDigest,
    DecisionMetadata,
    EvidenceReference,
    Hypothesis,
    HypothesisCategory,
    HypothesisReference,
    Quality,
    QualityLevel,
    Scenario,
    ScenarioCategory,
    ScenarioReference,
    Uncertainty,
    Validity,
    ValidityLevel,
)
from epip.decision.evidence import EvidenceRegistry


class InferenceLifecycleState(StrEnum):
    """Official lifecycle shared by hypotheses and scenarios."""

    CREATED = "created"
    SUPPORTED = "supported"
    VALIDATED = "validated"
    REGISTERED = "registered"
    AVAILABLE = "available"
    SNAPSHOTTED = "snapshotted"
    ARCHIVED = "archived"
    DISCARDED = "discarded"


_TRANSITIONS: Mapping[InferenceLifecycleState, InferenceLifecycleState] = MappingProxyType(
    {
        InferenceLifecycleState.CREATED: InferenceLifecycleState.SUPPORTED,
        InferenceLifecycleState.SUPPORTED: InferenceLifecycleState.VALIDATED,
        InferenceLifecycleState.VALIDATED: InferenceLifecycleState.REGISTERED,
        InferenceLifecycleState.REGISTERED: InferenceLifecycleState.AVAILABLE,
        InferenceLifecycleState.AVAILABLE: InferenceLifecycleState.SNAPSHOTTED,
        InferenceLifecycleState.SNAPSHOTTED: InferenceLifecycleState.ARCHIVED,
        InferenceLifecycleState.ARCHIVED: InferenceLifecycleState.DISCARDED,
    }
)


def _canonical_json(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def _content(value: Hypothesis | Scenario) -> dict[str, object]:
    result = value.to_dict()
    result.pop("content_digest")
    return result


def _mapping(value: object, field: str) -> Mapping[str, object]:
    if not isinstance(value, Mapping):
        raise RelationshipIntegrityError(f"{field} must be an object")
    return value


def _sequence(value: object, field: str) -> tuple[object, ...]:
    if not isinstance(value, list | tuple):
        raise RelationshipIntegrityError(f"{field} must be an array")
    return tuple(value)


def _number(value: object) -> float:
    if not isinstance(value, str | int | float) or isinstance(value, bool):
        raise RelationshipIntegrityError("inference number must be numeric")
    return float(value)


def _integer(value: object) -> int:
    if not isinstance(value, str | int) or isinstance(value, bool):
        raise RelationshipIntegrityError("inference integer must be numeric")
    return int(value)


def _reference[ReferenceT: (EvidenceReference, HypothesisReference, ScenarioReference)](
    value: object, value_type: type[ReferenceT]
) -> ReferenceT:
    value = _mapping(value, "inference reference")
    return value_type(identifier=str(value["identifier"]), version=_integer(value["version"]))


def _scores(value: Mapping[str, object]) -> tuple[Confidence, Quality, Validity, Uncertainty]:
    confidence = value["confidence"]
    quality = value["quality"]
    validity = value["validity"]
    uncertainty = value["uncertainty"]
    confidence = _mapping(confidence, "confidence")
    quality = _mapping(quality, "quality")
    validity = _mapping(validity, "validity")
    uncertainty = _mapping(uncertainty, "uncertainty")
    return (
        Confidence(_number(confidence["value"]), ConfidenceLevel(str(confidence["level"]))),
        Quality(_number(quality["value"]), QualityLevel(str(quality["level"]))),
        Validity(_number(validity["value"]), ValidityLevel(str(validity["level"]))),
        Uncertainty(_number(uncertainty["value"])),
    )


def _metadata(value: object) -> DecisionMetadata:
    value = _mapping(value, "inference metadata")
    return DecisionMetadata(
        _integer(value["version"]), str(value["logical_timestamp"]), str(value["source"])
    )


def _decision_digest(value: object) -> DecisionDigest:
    value = _mapping(value, "content digest")
    return DecisionDigest(str(value["value"]), str(value["algorithm"]))


def _hypothesis_from_dict(value: Mapping[str, object]) -> Hypothesis:
    confidence, quality, validity, uncertainty = _scores(value)
    return Hypothesis(
        hypothesis_id=str(value["hypothesis_id"]),
        category=HypothesisCategory(str(value["category"])),
        evidence=tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(value["evidence"], "hypothesis evidence")
        ),
        supporting_evidence=tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(value["supporting_evidence"], "hypothesis supporting evidence")
        ),
        contradicting_evidence=tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(
                value["contradicting_evidence"], "hypothesis contradicting evidence"
            )
        ),
        assumptions=tuple(
            str(item) for item in _sequence(value["assumptions"], "hypothesis assumptions")
        ),
        invalidation_conditions=tuple(
            str(item)
            for item in _sequence(
                value["invalidation_conditions"], "hypothesis invalidation conditions"
            )
        ),
        confidence=confidence,
        quality=quality,
        validity=validity,
        uncertainty=uncertainty,
        metadata=_metadata(value["metadata"]),
        content_digest=_decision_digest(value["content_digest"]),
    )


def _scenario_from_dict(value: Mapping[str, object]) -> Scenario:
    confidence, quality, validity, uncertainty = _scores(value)
    return Scenario(
        scenario_id=str(value["scenario_id"]),
        category=ScenarioCategory(str(value["category"])),
        hypotheses=tuple(
            _reference(item, HypothesisReference)
            for item in _sequence(value["hypotheses"], "scenario hypotheses")
        ),
        parent_scenarios=tuple(
            _reference(item, ScenarioReference)
            for item in _sequence(value["parent_scenarios"], "parent scenarios")
        ),
        supporting_evidence=tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(value["supporting_evidence"], "scenario supporting evidence")
        ),
        contradicting_evidence=tuple(
            _reference(item, EvidenceReference)
            for item in _sequence(
                value["contradicting_evidence"], "scenario contradicting evidence"
            )
        ),
        assumptions=tuple(
            str(item) for item in _sequence(value["assumptions"], "scenario assumptions")
        ),
        invalidation_conditions=tuple(
            str(item)
            for item in _sequence(
                value["invalidation_conditions"], "scenario invalidation conditions"
            )
        ),
        ranking_inputs=_ranking_inputs(value["ranking_inputs"]),
        confidence=confidence,
        quality=quality,
        validity=validity,
        uncertainty=uncertainty,
        metadata=_metadata(value["metadata"]),
        content_digest=_decision_digest(value["content_digest"]),
    )


def _ranking_inputs(value: object) -> tuple[tuple[str, float], ...]:
    result: list[tuple[str, float]] = []
    for item in _sequence(value, "scenario ranking inputs"):
        pair = _sequence(item, "scenario ranking input")
        if len(pair) != 2:
            raise RelationshipIntegrityError("scenario ranking input must be a pair")
        result.append((str(pair[0]), _number(pair[1])))
    return tuple(result)


@dataclass(frozen=True, slots=True)
class InferenceDigest:
    """Canonical SHA-256 digest for inference state."""

    value: str
    algorithm: str = "sha256"

    def __post_init__(self) -> None:
        if self.algorithm != "sha256" or len(self.value) != 64:
            raise RelationshipIntegrityError("inference digest must be SHA-256")
        try:
            int(self.value, 16)
        except ValueError as exc:
            raise RelationshipIntegrityError("inference digest must be hexadecimal") from exc

    @classmethod
    def from_value(cls, value: object) -> InferenceDigest:
        """Digest canonical JSON-compatible content."""
        return cls(hashlib.sha256(_canonical_json(value).encode("utf-8")).hexdigest())


@dataclass(frozen=True, slots=True)
class InferenceCollection:
    """Immutable identifier-ordered hypothesis collection."""

    items: tuple[Hypothesis, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise RelationshipIntegrityError("hypothesis collection must use a tuple")
        if any(not isinstance(item, Hypothesis) for item in self.items):
            raise RelationshipIntegrityError("hypothesis collection contains invalid value")
        ordered = tuple(sorted(self.items, key=lambda item: item.hypothesis_id))
        identifiers = tuple(item.hypothesis_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate hypothesis identifier")
        object.__setattr__(self, "items", ordered)

    def __iter__(self) -> Iterator[Hypothesis]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> Hypothesis | None:
        return next((item for item in self.items if item.hypothesis_id == identifier), None)

    def by_category(self, category: HypothesisCategory) -> InferenceCollection:
        return InferenceCollection(tuple(item for item in self.items if item.category is category))

    def by_evidence(self, reference: EvidenceReference) -> InferenceCollection:
        return InferenceCollection(tuple(item for item in self.items if reference in item.evidence))

    def group_by_category(self) -> tuple[tuple[HypothesisCategory, InferenceCollection], ...]:
        return tuple(
            (category, group)
            for category in HypothesisCategory
            if (group := self.by_category(category)).items
        )


HypothesisCollection = InferenceCollection


@dataclass(frozen=True, slots=True)
class ScenarioCollection:
    """Immutable identifier-ordered scenario collection."""

    items: tuple[Scenario, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.items, tuple):
            raise RelationshipIntegrityError("scenario collection must use a tuple")
        if any(not isinstance(item, Scenario) for item in self.items):
            raise RelationshipIntegrityError("scenario collection contains invalid value")
        ordered = tuple(sorted(self.items, key=lambda item: item.scenario_id))
        identifiers = tuple(item.scenario_id for item in ordered)
        if len(identifiers) != len(set(identifiers)):
            raise RelationshipIntegrityError("duplicate scenario identifier")
        object.__setattr__(self, "items", ordered)

    def __iter__(self) -> Iterator[Scenario]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def get(self, identifier: str) -> Scenario | None:
        return next((item for item in self.items if item.scenario_id == identifier), None)

    def by_category(self, category: ScenarioCategory) -> ScenarioCollection:
        return ScenarioCollection(tuple(item for item in self.items if item.category is category))

    def by_hypothesis(self, reference: HypothesisReference) -> ScenarioCollection:
        return ScenarioCollection(
            tuple(item for item in self.items if reference in item.hypotheses)
        )

    def group_by_category(self) -> tuple[tuple[ScenarioCategory, ScenarioCollection], ...]:
        return tuple(
            (category, group)
            for category in ScenarioCategory
            if (group := self.by_category(category)).items
        )


class InferenceValidator:
    """Structural validator with no market or financial interpretation."""

    def validate_hypothesis(
        self, hypothesis: Hypothesis, evidence_registry: EvidenceRegistry
    ) -> None:
        references = hypothesis.evidence
        if len(references) != len(set(references)):
            raise RelationshipIntegrityError("duplicate hypothesis evidence reference")
        if any(evidence_registry.by_reference(reference) is None for reference in references):
            raise RelationshipIntegrityError("unknown hypothesis evidence reference")
        if not set(hypothesis.supporting_evidence).issubset(references):
            raise RelationshipIntegrityError("supporting evidence must belong to hypothesis")
        if not set(hypothesis.contradicting_evidence).issubset(references):
            raise RelationshipIntegrityError("contradicting evidence must belong to hypothesis")
        if set(hypothesis.supporting_evidence) & set(hypothesis.contradicting_evidence):
            raise RelationshipIntegrityError(
                "evidence cannot support and contradict simultaneously"
            )
        if (
            DecisionDigest(InferenceDigest.from_value(_content(hypothesis)).value)
            != hypothesis.content_digest
        ):
            raise RelationshipIntegrityError("hypothesis content digest mismatch")

    def validate_scenario(
        self,
        scenario: Scenario,
        hypotheses: HypothesisRegistry,
        scenarios: ScenarioRegistry,
        evidence_registry: EvidenceRegistry,
    ) -> None:
        if len(scenario.hypotheses) != len(set(scenario.hypotheses)):
            raise RelationshipIntegrityError("duplicate scenario hypothesis reference")
        if len(scenario.parent_scenarios) != len(set(scenario.parent_scenarios)):
            raise RelationshipIntegrityError("duplicate parent scenario reference")
        if any(
            reference.identifier == scenario.scenario_id for reference in scenario.parent_scenarios
        ):
            raise RelationshipIntegrityError("scenario cannot reference itself")
        if any(hypotheses.by_reference(reference) is None for reference in scenario.hypotheses):
            raise RelationshipIntegrityError("unknown scenario hypothesis reference")
        if any(
            scenarios.by_reference(reference) is None for reference in scenario.parent_scenarios
        ):
            raise RelationshipIntegrityError("unknown parent scenario reference")
        evidence = scenario.supporting_evidence + scenario.contradicting_evidence
        if any(evidence_registry.by_reference(reference) is None for reference in evidence):
            raise RelationshipIntegrityError("unknown scenario evidence reference")
        if set(scenario.supporting_evidence) & set(scenario.contradicting_evidence):
            raise RelationshipIntegrityError("scenario evidence cannot support and contradict")
        if scenario.ranking_inputs:
            raise RelationshipIntegrityError("inference scenarios cannot contain ranking inputs")
        if (
            DecisionDigest(InferenceDigest.from_value(_content(scenario)).value)
            != scenario.content_digest
        ):
            raise RelationshipIntegrityError("scenario content digest mismatch")


@dataclass(frozen=True, slots=True)
class HypothesisBuilder:
    """Build one immutable hypothesis from explicit evidence interpretation."""

    def build(
        self,
        *,
        hypothesis_id: str,
        category: HypothesisCategory,
        evidence: tuple[EvidenceReference, ...],
        supporting_evidence: tuple[EvidenceReference, ...],
        contradicting_evidence: tuple[EvidenceReference, ...],
        assumptions: tuple[str, ...],
        invalidation_conditions: tuple[str, ...],
        confidence: Confidence,
        quality: Quality,
        validity: Validity,
        uncertainty: Uncertainty,
        metadata: DecisionMetadata,
    ) -> Hypothesis:
        provisional = Hypothesis(
            hypothesis_id,
            category,
            tuple(sorted(evidence, key=lambda item: (item.identifier, item.version))),
            tuple(sorted(supporting_evidence, key=lambda item: (item.identifier, item.version))),
            tuple(sorted(contradicting_evidence, key=lambda item: (item.identifier, item.version))),
            assumptions,
            invalidation_conditions,
            confidence,
            quality,
            validity,
            uncertainty,
            metadata,
            DecisionDigest("0" * 64),
        )
        return Hypothesis(
            hypothesis_id=provisional.hypothesis_id,
            category=provisional.category,
            evidence=provisional.evidence,
            supporting_evidence=provisional.supporting_evidence,
            contradicting_evidence=provisional.contradicting_evidence,
            assumptions=provisional.assumptions,
            invalidation_conditions=provisional.invalidation_conditions,
            confidence=provisional.confidence,
            quality=provisional.quality,
            validity=provisional.validity,
            uncertainty=provisional.uncertainty,
            metadata=provisional.metadata,
            content_digest=DecisionDigest(InferenceDigest.from_value(_content(provisional)).value),
        )


@dataclass(frozen=True, slots=True)
class ScenarioBuilder:
    """Assemble one scenario without ranking or selecting it."""

    def build(
        self,
        *,
        scenario_id: str,
        category: ScenarioCategory,
        hypotheses: tuple[HypothesisReference, ...],
        parent_scenarios: tuple[ScenarioReference, ...],
        supporting_evidence: tuple[EvidenceReference, ...],
        contradicting_evidence: tuple[EvidenceReference, ...],
        assumptions: tuple[str, ...],
        invalidation_conditions: tuple[str, ...],
        confidence: Confidence,
        quality: Quality,
        validity: Validity,
        uncertainty: Uncertainty,
        metadata: DecisionMetadata,
    ) -> Scenario:
        provisional = Scenario(
            scenario_id,
            category,
            tuple(sorted(hypotheses, key=lambda item: (item.identifier, item.version))),
            tuple(sorted(parent_scenarios, key=lambda item: (item.identifier, item.version))),
            tuple(sorted(supporting_evidence, key=lambda item: (item.identifier, item.version))),
            tuple(sorted(contradicting_evidence, key=lambda item: (item.identifier, item.version))),
            assumptions,
            invalidation_conditions,
            (),
            confidence,
            quality,
            validity,
            uncertainty,
            metadata,
            DecisionDigest("0" * 64),
        )
        return Scenario(
            scenario_id=provisional.scenario_id,
            category=provisional.category,
            hypotheses=provisional.hypotheses,
            parent_scenarios=provisional.parent_scenarios,
            supporting_evidence=provisional.supporting_evidence,
            contradicting_evidence=provisional.contradicting_evidence,
            assumptions=provisional.assumptions,
            invalidation_conditions=provisional.invalidation_conditions,
            ranking_inputs=provisional.ranking_inputs,
            confidence=provisional.confidence,
            quality=provisional.quality,
            validity=provisional.validity,
            uncertainty=provisional.uncertainty,
            metadata=provisional.metadata,
            content_digest=DecisionDigest(InferenceDigest.from_value(_content(provisional)).value),
        )


@dataclass(frozen=True, slots=True)
class _HypothesisEntry:
    hypothesis: Hypothesis
    state: InferenceLifecycleState


@dataclass(frozen=True, slots=True)
class HypothesisRegistry:
    """Immutable hypothesis registry and deterministic indexes."""

    entries: tuple[_HypothesisEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise RelationshipIntegrityError("hypothesis registry must use a tuple")
        if any(not isinstance(item, _HypothesisEntry) for item in self.entries):
            raise RelationshipIntegrityError("invalid hypothesis registry entry")
        ordered = tuple(sorted(self.entries, key=lambda item: item.hypothesis.hypothesis_id))
        ids = tuple(item.hypothesis.hypothesis_id for item in ordered)
        if len(ids) != len(set(ids)):
            raise RelationshipIntegrityError("duplicate hypothesis identifier")
        if any(not isinstance(item.state, InferenceLifecycleState) for item in ordered):
            raise RelationshipIntegrityError("invalid hypothesis lifecycle state")
        object.__setattr__(self, "entries", ordered)

    def register(self, hypothesis: Hypothesis, evidence: EvidenceRegistry) -> HypothesisRegistry:
        if self.get(hypothesis.hypothesis_id) is not None:
            raise RelationshipIntegrityError("duplicate hypothesis identifier")
        result = HypothesisRegistry(
            self.entries + (_HypothesisEntry(hypothesis, InferenceLifecycleState.CREATED),)
        )
        InferenceValidator().validate_hypothesis(hypothesis, evidence)
        for state in (
            InferenceLifecycleState.SUPPORTED,
            InferenceLifecycleState.VALIDATED,
            InferenceLifecycleState.REGISTERED,
        ):
            result = result.transition(hypothesis.hypothesis_id, state)
        return result

    def transition(self, identifier: str, target: InferenceLifecycleState) -> HypothesisRegistry:
        entry = self.entry(identifier)
        if _TRANSITIONS.get(entry.state) is not target:
            raise RelationshipIntegrityError(
                f"invalid hypothesis transition: {entry.state} -> {target}"
            )
        replacement = _HypothesisEntry(entry.hypothesis, target)
        return HypothesisRegistry(
            tuple(
                replacement if item.hypothesis.hypothesis_id == identifier else item
                for item in self.entries
            )
        )

    def entry(self, identifier: str) -> _HypothesisEntry:
        found = next(
            (item for item in self.entries if item.hypothesis.hypothesis_id == identifier), None
        )
        if found is None:
            raise KeyError(identifier)
        return found

    def get(self, identifier: str) -> Hypothesis | None:
        return next(
            (
                item.hypothesis
                for item in self.entries
                if item.hypothesis.hypothesis_id == identifier
            ),
            None,
        )

    def by_reference(self, reference: HypothesisReference) -> Hypothesis | None:
        value = self.get(reference.identifier)
        return value if value is not None and value.metadata.version == reference.version else None

    def by_type(self, value_type: type[Hypothesis]) -> InferenceCollection:
        return InferenceCollection(
            tuple(item.hypothesis for item in self.entries if type(item.hypothesis) is value_type)
        )

    def by_category(self, category: HypothesisCategory) -> InferenceCollection:
        return self.collection().by_category(category)

    def by_evidence(self, reference: EvidenceReference) -> InferenceCollection:
        return self.collection().by_evidence(reference)

    def by_digest(self, digest: str | DecisionDigest) -> Hypothesis | None:
        value = digest.value if isinstance(digest, DecisionDigest) else digest
        return next(
            (
                item.hypothesis
                for item in self.entries
                if item.hypothesis.content_digest.value == value
            ),
            None,
        )

    def collection(self, state: InferenceLifecycleState | None = None) -> InferenceCollection:
        return InferenceCollection(
            tuple(item.hypothesis for item in self.entries if state is None or item.state is state)
        )


@dataclass(frozen=True, slots=True)
class _ScenarioEntry:
    scenario: Scenario
    state: InferenceLifecycleState


@dataclass(frozen=True, slots=True)
class ScenarioRegistry:
    """Immutable scenario registry and deterministic indexes."""

    entries: tuple[_ScenarioEntry, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.entries, tuple):
            raise RelationshipIntegrityError("scenario registry must use a tuple")
        if any(not isinstance(item, _ScenarioEntry) for item in self.entries):
            raise RelationshipIntegrityError("invalid scenario registry entry")
        ordered = tuple(sorted(self.entries, key=lambda item: item.scenario.scenario_id))
        ids = tuple(item.scenario.scenario_id for item in ordered)
        if len(ids) != len(set(ids)):
            raise RelationshipIntegrityError("duplicate scenario identifier")
        if any(not isinstance(item.state, InferenceLifecycleState) for item in ordered):
            raise RelationshipIntegrityError("invalid scenario lifecycle state")
        object.__setattr__(self, "entries", ordered)

    def register(
        self, scenario: Scenario, hypotheses: HypothesisRegistry, evidence: EvidenceRegistry
    ) -> ScenarioRegistry:
        if self.get(scenario.scenario_id) is not None:
            raise RelationshipIntegrityError("duplicate scenario identifier")
        result = ScenarioRegistry(
            self.entries + (_ScenarioEntry(scenario, InferenceLifecycleState.CREATED),)
        )
        InferenceValidator().validate_scenario(scenario, hypotheses, self, evidence)
        for state in (
            InferenceLifecycleState.SUPPORTED,
            InferenceLifecycleState.VALIDATED,
            InferenceLifecycleState.REGISTERED,
        ):
            result = result.transition(scenario.scenario_id, state)
        return result

    def transition(self, identifier: str, target: InferenceLifecycleState) -> ScenarioRegistry:
        entry = self.entry(identifier)
        if _TRANSITIONS.get(entry.state) is not target:
            raise RelationshipIntegrityError(
                f"invalid scenario transition: {entry.state} -> {target}"
            )
        replacement = _ScenarioEntry(entry.scenario, target)
        return ScenarioRegistry(
            tuple(
                replacement if item.scenario.scenario_id == identifier else item
                for item in self.entries
            )
        )

    def entry(self, identifier: str) -> _ScenarioEntry:
        found = next(
            (item for item in self.entries if item.scenario.scenario_id == identifier), None
        )
        if found is None:
            raise KeyError(identifier)
        return found

    def get(self, identifier: str) -> Scenario | None:
        return next(
            (item.scenario for item in self.entries if item.scenario.scenario_id == identifier),
            None,
        )

    def by_reference(self, reference: ScenarioReference) -> Scenario | None:
        value = self.get(reference.identifier)
        return value if value is not None and value.metadata.version == reference.version else None

    def by_type(self, value_type: type[Scenario]) -> ScenarioCollection:
        return ScenarioCollection(
            tuple(item.scenario for item in self.entries if type(item.scenario) is value_type)
        )

    def by_category(self, category: ScenarioCategory) -> ScenarioCollection:
        return self.collection().by_category(category)

    def by_hypothesis(self, reference: HypothesisReference) -> ScenarioCollection:
        return self.collection().by_hypothesis(reference)

    def by_scenario(self, reference: ScenarioReference) -> ScenarioCollection:
        return ScenarioCollection(
            tuple(
                item.scenario
                for item in self.entries
                if reference in item.scenario.parent_scenarios
            )
        )

    def by_evidence(self, reference: EvidenceReference) -> ScenarioCollection:
        return ScenarioCollection(
            tuple(
                item.scenario
                for item in self.entries
                if reference
                in item.scenario.supporting_evidence + item.scenario.contradicting_evidence
            )
        )

    def by_digest(self, digest: str | DecisionDigest) -> Scenario | None:
        value = digest.value if isinstance(digest, DecisionDigest) else digest
        return next(
            (item.scenario for item in self.entries if item.scenario.content_digest.value == value),
            None,
        )

    def collection(self, state: InferenceLifecycleState | None = None) -> ScenarioCollection:
        return ScenarioCollection(
            tuple(item.scenario for item in self.entries if state is None or item.state is state)
        )


@dataclass(frozen=True, slots=True)
class InferenceSnapshot:
    """Immutable deterministic snapshot of inference registry state."""

    snapshot_id: str
    version: int
    hypotheses: tuple[tuple[Hypothesis, InferenceLifecycleState], ...]
    scenarios: tuple[tuple[Scenario, InferenceLifecycleState], ...]
    digest: InferenceDigest

    def __post_init__(self) -> None:
        require_text(self.snapshot_id, "inference.snapshot_id")
        require_version(self.version)
        if not isinstance(self.hypotheses, tuple) or not isinstance(self.scenarios, tuple):
            raise RelationshipIntegrityError("inference snapshot collections must use tuples")
        if any(
            not isinstance(value, Hypothesis) or not isinstance(state, InferenceLifecycleState)
            for value, state in self.hypotheses
        ):
            raise RelationshipIntegrityError("invalid hypothesis snapshot entry")
        if any(
            not isinstance(value, Scenario) or not isinstance(state, InferenceLifecycleState)
            for value, state in self.scenarios
        ):
            raise RelationshipIntegrityError("invalid scenario snapshot entry")
        payload = self._payload()
        if InferenceDigest.from_value(payload) != self.digest:
            raise RelationshipIntegrityError("inference snapshot digest mismatch")

    def _payload(self) -> dict[str, object]:
        return {
            "snapshot_id": self.snapshot_id,
            "version": self.version,
            "hypotheses": [
                {"value": value.to_dict(), "state": state.value} for value, state in self.hypotheses
            ],
            "scenarios": [
                {"value": value.to_dict(), "state": state.value} for value, state in self.scenarios
            ],
        }

    @classmethod
    def create(
        cls,
        snapshot_id: str,
        version: int,
        hypotheses: HypothesisRegistry,
        scenarios: ScenarioRegistry,
    ) -> InferenceSnapshot:
        require_text(snapshot_id, "inference.snapshot_id")
        require_version(version)
        hypothesis_data = tuple((item.hypothesis, item.state) for item in hypotheses.entries)
        scenario_data = tuple((item.scenario, item.state) for item in scenarios.entries)
        payload = {
            "snapshot_id": snapshot_id,
            "version": version,
            "hypotheses": [
                {"value": value.to_dict(), "state": state.value} for value, state in hypothesis_data
            ],
            "scenarios": [
                {"value": value.to_dict(), "state": state.value} for value, state in scenario_data
            ],
        }
        return cls(
            snapshot_id,
            version,
            hypothesis_data,
            scenario_data,
            InferenceDigest.from_value(payload),
        )

    def to_json(self) -> str:
        return _canonical_json(
            self._payload()
            | {"digest": {"value": self.digest.value, "algorithm": self.digest.algorithm}}
        )

    @classmethod
    def from_json(cls, value: str) -> InferenceSnapshot:
        """Rebuild and validate a snapshot from canonical JSON."""
        try:
            data = json.loads(value)
            if not isinstance(data, Mapping):
                raise RelationshipIntegrityError("inference snapshot must be an object")
            hypotheses = tuple(
                (
                    _hypothesis_from_dict(
                        _mapping(
                            _mapping(item, "hypothesis snapshot entry")["value"],
                            "hypothesis snapshot value",
                        )
                    ),
                    InferenceLifecycleState(
                        str(_mapping(item, "hypothesis snapshot entry")["state"])
                    ),
                )
                for item in _sequence(data["hypotheses"], "snapshot hypotheses")
            )
            scenarios = tuple(
                (
                    _scenario_from_dict(
                        _mapping(
                            _mapping(item, "scenario snapshot entry")["value"],
                            "scenario snapshot value",
                        )
                    ),
                    InferenceLifecycleState(
                        str(_mapping(item, "scenario snapshot entry")["state"])
                    ),
                )
                for item in _sequence(data["scenarios"], "snapshot scenarios")
            )
            digest_data = data["digest"]
            if not isinstance(digest_data, Mapping):
                raise RelationshipIntegrityError("inference snapshot digest must be an object")
            return cls(
                str(data["snapshot_id"]),
                int(data["version"]),
                hypotheses,
                scenarios,
                InferenceDigest(str(digest_data["value"]), str(digest_data["algorithm"])),
            )
        except (KeyError, TypeError, ValueError) as exc:
            raise RelationshipIntegrityError("invalid inference snapshot") from exc


@dataclass(frozen=True, slots=True)
class InferenceStatistics:
    hypotheses: int
    scenarios: int
    hypothesis_categories: tuple[tuple[str, int], ...]
    scenario_categories: tuple[tuple[str, int], ...]
    rejections: int


@dataclass(frozen=True, slots=True)
class InferenceAudit:
    statistics: InferenceStatistics
    hypothesis_ids: tuple[str, ...]
    scenario_ids: tuple[str, ...]
    rejection_messages: tuple[str, ...]


@dataclass(frozen=True, slots=True)
class InferenceDiagnostics:
    """Read-only diagnostics; it never repairs state."""

    def inspect(self, engine: InferenceEngine) -> tuple[str, ...]:
        issues = list(engine.rejection_messages)
        for entry in engine.hypotheses.entries:
            try:
                InferenceValidator().validate_hypothesis(entry.hypothesis, engine.evidence)
            except RelationshipIntegrityError as exc:
                issues.append(f"{entry.hypothesis.hypothesis_id}: {exc}")
        for scenario_entry in engine.scenarios.entries:
            try:
                InferenceValidator().validate_scenario(
                    scenario_entry.scenario,
                    engine.hypotheses,
                    engine.scenarios,
                    engine.evidence,
                )
            except RelationshipIntegrityError as exc:
                issues.append(f"{scenario_entry.scenario.scenario_id}: {exc}")
        return tuple(issues)


@dataclass(frozen=True, slots=True)
class InferenceEngine:
    """Immutable coordinator for structural hypothesis and scenario inference."""

    evidence: EvidenceRegistry
    hypotheses: HypothesisRegistry = HypothesisRegistry()
    scenarios: ScenarioRegistry = ScenarioRegistry()
    rejection_messages: tuple[str, ...] = ()

    def register_hypothesis(self, value: Hypothesis) -> InferenceEngine:
        return InferenceEngine(
            self.evidence,
            self.hypotheses.register(value, self.evidence),
            self.scenarios,
            self.rejection_messages,
        )

    def register_scenario(self, value: Scenario) -> InferenceEngine:
        return InferenceEngine(
            self.evidence,
            self.hypotheses,
            self.scenarios.register(value, self.hypotheses, self.evidence),
            self.rejection_messages,
        )

    def try_register_hypothesis(self, value: Hypothesis) -> tuple[InferenceEngine, bool]:
        try:
            return self.register_hypothesis(value), True
        except RelationshipIntegrityError as exc:
            return (
                InferenceEngine(
                    self.evidence,
                    self.hypotheses,
                    self.scenarios,
                    self.rejection_messages + (str(exc),),
                ),
                False,
            )

    def try_register_scenario(self, value: Scenario) -> tuple[InferenceEngine, bool]:
        try:
            return self.register_scenario(value), True
        except RelationshipIntegrityError as exc:
            return (
                InferenceEngine(
                    self.evidence,
                    self.hypotheses,
                    self.scenarios,
                    self.rejection_messages + (str(exc),),
                ),
                False,
            )

    def make_hypothesis_available(self, identifier: str) -> InferenceEngine:
        return InferenceEngine(
            self.evidence,
            self.hypotheses.transition(identifier, InferenceLifecycleState.AVAILABLE),
            self.scenarios,
            self.rejection_messages,
        )

    def make_scenario_available(self, identifier: str) -> InferenceEngine:
        return InferenceEngine(
            self.evidence,
            self.hypotheses,
            self.scenarios.transition(identifier, InferenceLifecycleState.AVAILABLE),
            self.rejection_messages,
        )

    def snapshot(
        self, snapshot_id: str, version: int = 1
    ) -> tuple[InferenceEngine, InferenceSnapshot]:
        hypotheses = self.hypotheses
        scenarios = self.scenarios
        for hypothesis_entry in hypotheses.entries:
            if hypothesis_entry.state is InferenceLifecycleState.AVAILABLE:
                hypotheses = hypotheses.transition(
                    hypothesis_entry.hypothesis.hypothesis_id,
                    InferenceLifecycleState.SNAPSHOTTED,
                )
        for scenario_entry in scenarios.entries:
            if scenario_entry.state is InferenceLifecycleState.AVAILABLE:
                scenarios = scenarios.transition(
                    scenario_entry.scenario.scenario_id,
                    InferenceLifecycleState.SNAPSHOTTED,
                )
        engine = InferenceEngine(self.evidence, hypotheses, scenarios, self.rejection_messages)
        return engine, InferenceSnapshot.create(snapshot_id, version, hypotheses, scenarios)

    def audit(self) -> InferenceAudit:
        h_categories = tuple(
            (category.value, len(self.hypotheses.by_category(category)))
            for category in HypothesisCategory
            if self.hypotheses.by_category(category).items
        )
        s_categories = tuple(
            (category.value, len(self.scenarios.by_category(category)))
            for category in ScenarioCategory
            if self.scenarios.by_category(category).items
        )
        return InferenceAudit(
            InferenceStatistics(
                len(self.hypotheses.entries),
                len(self.scenarios.entries),
                h_categories,
                s_categories,
                len(self.rejection_messages),
            ),
            tuple(item.hypothesis.hypothesis_id for item in self.hypotheses.entries),
            tuple(item.scenario.scenario_id for item in self.scenarios.entries),
            self.rejection_messages,
        )


__all__ = [
    "HypothesisBuilder",
    "HypothesisCollection",
    "HypothesisRegistry",
    "InferenceAudit",
    "InferenceCollection",
    "InferenceDiagnostics",
    "InferenceDigest",
    "InferenceEngine",
    "InferenceLifecycleState",
    "InferenceSnapshot",
    "InferenceStatistics",
    "InferenceValidator",
    "ScenarioBuilder",
    "ScenarioCollection",
    "ScenarioRegistry",
]
