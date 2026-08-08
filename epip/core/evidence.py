"""Evidence value objects for the core domain."""

from __future__ import annotations

import json
from collections.abc import Mapping
from dataclasses import InitVar, dataclass, field
from typing import Any

from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import (
    deep_freeze,
    deep_thaw,
    integrity_deserializer,
    require_text,
    require_version,
)
from epip.core.types import Direction
from epip.core.value_objects import Confidence


@dataclass(frozen=True, slots=True)
class Evidence:
    """A single piece of evidence produced by a plugin.

    Args:
        id: Unique evidence identifier.
        source: Plugin or source that produced the evidence.
        category: Evidence category.
        direction: Direction inferred by the evidence.
        confidence: Confidence score between 0 and 1.
        timestamp: Evidence creation timestamp.
        metadata: Additional structured metadata.
    """

    id: str
    source: str
    category: str
    direction: Direction
    confidence: Confidence | float
    timestamp: str
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False)
    schema_version: int = field(default=1, compare=False)
    created_at: str = field(default="", compare=False)
    uuid: str = field(default="", compare=False)
    clock: InitVar[ClockProtocol | None] = None
    id_generator: InitVar[IdGeneratorProtocol | None] = None

    def __post_init__(
        self, clock: ClockProtocol | None, id_generator: IdGeneratorProtocol | None
    ) -> None:
        """Validate the evidence values and freeze metadata."""
        object.__setattr__(self, "confidence", Confidence(self.confidence))
        object.__setattr__(self, "created_at", self.created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            self.uuid or resolve_id_generator(id_generator).generate("evidence", self.id),
        )
        object.__setattr__(self, "metadata", deep_freeze(self.metadata))
        require_text(self.id, "evidence.id")
        require_text(self.source, "evidence.source")
        require_text(self.category, "evidence.category")
        require_text(self.timestamp, "evidence.timestamp")
        require_version(self.schema_version, "evidence.schema_version")

    def to_dict(self) -> dict[str, Any]:
        """Serialize the evidence to a dictionary."""
        return {
            "id": self.id,
            "source": self.source,
            "category": self.category,
            "direction": self.direction.value,
            "confidence": float(self.confidence),
            "timestamp": self.timestamp,
            "metadata": deep_thaw(self.metadata),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    @integrity_deserializer
    def from_dict(cls, data: dict[str, Any]) -> Evidence:
        """Deserialize the evidence from a dictionary."""
        return cls(
            id=data["id"],
            source=data["source"],
            category=data["category"],
            direction=Direction(data["direction"]),
            confidence=data.get("confidence", 0.0),
            timestamp=data["timestamp"],
            metadata=data.get("metadata", {}),
            schema_version=data.get("schema_version", 1),
            created_at=data.get("created_at", ""),
            uuid=data.get("uuid", ""),
        )

    def to_json(self) -> str:
        """Serialize the evidence to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    @integrity_deserializer
    def from_json(cls, payload: str) -> Evidence:
        """Deserialize the evidence from JSON."""
        return cls.from_dict(json.loads(payload))
