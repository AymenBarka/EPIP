"""Lightweight numeric value objects used by the core domain."""

from __future__ import annotations

import json
from datetime import UTC, datetime
from typing import Any, Self
from uuid import uuid4


def _utc_now() -> str:
    """Return a UTC timestamp suitable for domain persistence."""
    return datetime.now(UTC).isoformat()


class _DomainValue(float):
    """Base class for immutable domain value objects backed by a float."""

    __slots__ = ("created_at", "schema_version", "uuid")

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> Self:
        return super().__new__(cls, float(value))

    def __init__(
        self,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> None:
        self.schema_version = schema_version
        self.created_at = created_at or _utc_now()
        self.uuid = uuid_value or uuid4().hex

    def to_dict(self) -> dict[str, Any]:
        """Serialize the value object into a dictionary."""
        return {
            "value": float(self),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any] | float) -> _DomainValue:
        """Deserialize the value object from a dictionary or scalar."""
        if isinstance(data, (float, int)):
            return cls(float(data))
        if isinstance(data, dict):
            return cls(
                data.get("value", 0.0),
                schema_version=data.get("schema_version", 1),
                created_at=data.get("created_at", ""),
                uuid_value=data.get("uuid", ""),
            )
        raise TypeError("unsupported value object payload")

    def to_json(self) -> str:
        """Serialize the value object to JSON."""
        return json.dumps(self.to_dict(), sort_keys=True)

    @classmethod
    def from_json(cls, payload: str) -> _DomainValue:
        """Deserialize the value object from JSON."""
        return cls.from_dict(json.loads(payload))


class Confidence(_DomainValue):
    """Confidence score restricted to the [0.0, 1.0] interval."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> Self:
        numeric_value = float(value)
        if not 0.0 <= numeric_value <= 1.0:
            raise ValueError("confidence must be between 0 and 1")
        return super().__new__(cls, numeric_value, schema_version, created_at, uuid_value)


class Probability(_DomainValue):
    """Probability score restricted to the [0.0, 1.0] interval."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> Self:
        numeric_value = float(value)
        if not 0.0 <= numeric_value <= 1.0:
            raise ValueError("probability must be between 0 and 1")
        return super().__new__(cls, numeric_value, schema_version, created_at, uuid_value)


class RiskScore(_DomainValue):
    """Risk score restricted to the [0.0, 1.0] interval."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> Self:
        numeric_value = float(value)
        if not 0.0 <= numeric_value <= 1.0:
            raise ValueError("risk_score must be between 0 and 1")
        return super().__new__(cls, numeric_value, schema_version, created_at, uuid_value)


class Price(_DomainValue):
    """Price value object restricted to non-negative values."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
    ) -> Self:
        numeric_value = float(value)
        if numeric_value < 0.0:
            raise ValueError("price must be non-negative")
        return super().__new__(cls, numeric_value, schema_version, created_at, uuid_value)
