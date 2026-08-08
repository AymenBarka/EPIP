"""Decision value objects for the core domain."""

from __future__ import annotations

import json
from dataclasses import InitVar, dataclass, field
from typing import Any

from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.types import DecisionType
from epip.core.value_objects import Probability, RiskScore


@dataclass(frozen=True, slots=True)
class Decision:
    """A final decision emitted by the decision engine.

    Args:
        id: Unique decision identifier.
        decision_type: Final decision direction.
        reason: Explanation for the decision.
        probability: Decision probability.
        risk_score: Associated risk score.
        timestamp: Decision creation timestamp.
    """

    id: str
    decision_type: DecisionType
    reason: str
    probability: Probability | float = field(default_factory=lambda: Probability(0.0))
    risk_score: RiskScore | float = field(default_factory=lambda: RiskScore(0.0))
    timestamp: str = ""
    schema_version: int = field(default=1, compare=False)
    created_at: str = field(default="", compare=False)
    uuid: str = field(default="", compare=False)
    clock: InitVar[ClockProtocol | None] = None
    id_generator: InitVar[IdGeneratorProtocol | None] = None

    def __post_init__(
        self, clock: ClockProtocol | None, id_generator: IdGeneratorProtocol | None
    ) -> None:
        """Validate the probability and risk values."""
        object.__setattr__(self, "probability", Probability(self.probability))
        object.__setattr__(self, "risk_score", RiskScore(self.risk_score))
        object.__setattr__(self, "created_at", self.created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            self.uuid or resolve_id_generator(id_generator).generate("decision", self.id),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the decision to a dictionary."""
        return {
            "id": self.id,
            "decision_type": self.decision_type.value,
            "reason": self.reason,
            "probability": float(self.probability),
            "risk_score": float(self.risk_score),
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Decision:
        """Deserialize the decision from a dictionary."""
        return cls(
            id=data["id"],
            decision_type=DecisionType(data["decision_type"]),
            reason=data["reason"],
            probability=data.get("probability", 0.0),
            risk_score=data.get("risk_score", 0.0),
            timestamp=data.get("timestamp", ""),
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the decision to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Decision:
        """Deserialize the decision from JSON."""
        return cls.from_dict(json.loads(payload))
