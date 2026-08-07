"""Hypothesis value objects for the core domain."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any
from uuid import uuid4

from epip.core.scenario import Scenario


@dataclass(frozen=True, slots=True)
class Hypothesis:
    """An hypothesis derived from a scenario.

    Args:
        id: Unique hypothesis identifier.
        scenario: The source scenario.
        timestamp: Hypothesis creation timestamp.
    """

    id: str
    scenario: Scenario
    timestamp: str
    schema_version: int = 1
    created_at: str = ""
    uuid: str = ""

    def __post_init__(self) -> None:
        """Populate metadata for the hypothesis."""
        object.__setattr__(self, "created_at", self.created_at or datetime.now(UTC).isoformat())
        object.__setattr__(self, "uuid", self.uuid or uuid4().hex)

    def to_dict(self) -> dict[str, Any]:
        """Serialize the hypothesis to a dictionary."""
        return {
            "id": self.id,
            "scenario": self.scenario.to_dict(),
            "timestamp": self.timestamp,
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Hypothesis:
        """Deserialize the hypothesis from a dictionary."""
        return cls(
            id=data["id"],
            scenario=Scenario.from_dict(data["scenario"]),
            timestamp=data["timestamp"],
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the hypothesis to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> Hypothesis:
        """Deserialize the hypothesis from JSON."""
        return cls.from_dict(json.loads(payload))
