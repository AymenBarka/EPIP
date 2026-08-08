"""Domain events for the core layer."""

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


@dataclass(frozen=True, slots=True, kw_only=True)
class BaseEvent:
    """Base class for domain events."""

    id: str
    timestamp: str
    schema_version: int = field(default=1, compare=False)
    created_at: str = field(default="", compare=False)
    uuid: str = field(default="", compare=False)
    clock: InitVar[ClockProtocol | None] = None
    id_generator: InitVar[IdGeneratorProtocol | None] = None

    def __post_init__(
        self, clock: ClockProtocol | None, id_generator: IdGeneratorProtocol | None
    ) -> None:
        """Populate metadata for the event."""
        object.__setattr__(self, "created_at", self.created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            self.uuid
            or resolve_id_generator(id_generator).generate("event", self.id, self.timestamp),
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        return {
            "id": self.id,
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> BaseEvent:
        """Deserialize the event from a dictionary."""
        payload: dict[str, Any] = {
            "id": data["id"],
            "timestamp": data["timestamp"],
            "schema_version": data.get("schema_version", 1),
            "created_at": data.get("created_at", ""),
            "uuid": data.get("uuid", ""),
        }
        for field_name in ("evidence_id", "scenario_id", "decision_id", "reason"):
            if field_name in data:
                payload[field_name] = data[field_name]
        return cls(**payload)

    def to_json(self) -> str:
        """Serialize the event to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> BaseEvent:
        """Deserialize the event from JSON."""
        return cls.from_dict(json.loads(payload))


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceCreated(BaseEvent):
    """Raised when evidence is created."""

    evidence_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["evidence_id"] = self.evidence_id
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ScenarioCreated(BaseEvent):
    """Raised when a scenario is created."""

    scenario_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["scenario_id"] = self.scenario_id
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionCreated(BaseEvent):
    """Raised when a decision is created."""

    decision_id: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["decision_id"] = self.decision_id
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class EvidenceRejected(BaseEvent):
    """Raised when evidence is rejected."""

    evidence_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["evidence_id"] = self.evidence_id
        payload["reason"] = self.reason
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class ScenarioRejected(BaseEvent):
    """Raised when a scenario is rejected."""

    scenario_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["scenario_id"] = self.scenario_id
        payload["reason"] = self.reason
        return payload


@dataclass(frozen=True, slots=True, kw_only=True)
class DecisionRejected(BaseEvent):
    """Raised when a decision is rejected."""

    decision_id: str
    reason: str

    def to_dict(self) -> dict[str, Any]:
        """Serialize the event to a dictionary."""
        payload = super().to_dict()
        payload["decision_id"] = self.decision_id
        payload["reason"] = self.reason
        return payload
