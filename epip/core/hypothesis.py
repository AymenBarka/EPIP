"""Hypothesis value objects for the core domain."""

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
from epip.core.integrity import integrity_deserializer
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
    schema_version: int = field(default=1, compare=False)
    created_at: str = field(default="", compare=False)
    uuid: str = field(default="", compare=False)
    clock: InitVar[ClockProtocol | None] = None
    id_generator: InitVar[IdGeneratorProtocol | None] = None

    def __post_init__(
        self, clock: ClockProtocol | None, id_generator: IdGeneratorProtocol | None
    ) -> None:
        """Populate metadata for the hypothesis."""
        object.__setattr__(self, "created_at", self.created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            self.uuid or resolve_id_generator(id_generator).generate("hypothesis", self.id),
        )

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
    @integrity_deserializer
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
    @integrity_deserializer
    def from_json(cls, payload: str) -> Hypothesis:
        """Deserialize the hypothesis from JSON."""
        return cls.from_dict(json.loads(payload))
