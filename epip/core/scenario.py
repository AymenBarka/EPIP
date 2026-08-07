"""Scenario value objects for the core domain."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from epip.core.evidence import Evidence
from epip.core.types import Direction, ScenarioType
from epip.core.value_objects import Probability


@dataclass(frozen=True, slots=True)
class Scenario:
    """A scenario built from one or more evidences.

    Args:
        id: Unique scenario identifier.
        direction: Scenario direction.
        scenario_type: Scenario classification.
        evidence: Evidence items supporting the scenario.
        probability: Scenario probability score.
        timestamp: Scenario creation timestamp.
    """

    id: str
    direction: Direction
    scenario_type: ScenarioType
    evidence: tuple[Evidence, ...] | list[Evidence] = field(default_factory=tuple)
    global_score: float = 0.0
    probability: Probability | float = field(default_factory=lambda: Probability(0.0))
    timestamp: str = ""
    schema_version: int = 1
    created_at: str = ""
    uuid: str = ""

    def __post_init__(self) -> None:
        """Normalize evidence and compute the average evidence score."""
        normalized_evidence = tuple(self.evidence)
        object.__setattr__(self, "evidence", normalized_evidence)
        object.__setattr__(self, "probability", Probability(self.probability))
        object.__setattr__(self, "created_at", self.created_at or datetime.now(UTC).isoformat())
        object.__setattr__(self, "uuid", self.uuid or uuid4().hex)

        if normalized_evidence:
            score = sum(float(item.confidence) for item in normalized_evidence) / len(
                normalized_evidence
            )
        else:
            score = float(self.probability)
        object.__setattr__(self, "global_score", score)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the scenario to a dictionary."""
        return {
            "id": self.id,
            "direction": self.direction.value,
            "scenario_type": self.scenario_type.value,
            "evidence": [item.to_dict() for item in self.evidence],
            "global_score": self.global_score,
            "probability": float(self.probability),
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Scenario:
        """Deserialize the scenario from a dictionary."""
        return cls(
            id=data["id"],
            direction=Direction(data["direction"]),
            scenario_type=ScenarioType(data["scenario_type"]),
            evidence=tuple(Evidence.from_dict(item) for item in data.get("evidence", [])),
            probability=data.get("probability", 0.0),
            timestamp=data["timestamp"],
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the scenario to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Scenario:
        """Deserialize the scenario from JSON."""
        return cls.from_dict(json.loads(payload))
