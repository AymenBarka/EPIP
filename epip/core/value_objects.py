"""Lightweight numeric value objects used by the core domain."""

from __future__ import annotations

import json
from typing import Any, Self

from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)
from epip.core.integrity import (
    integrity_deserializer,
    require_finite,
    require_non_negative,
    require_unit_interval,
    require_version,
)


class _DomainValue(float):
    """Base class for immutable domain value objects backed by a float."""

    schema_version: int
    created_at: str
    uuid: str
    __slots__ = ("created_at", "schema_version", "uuid")

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> Self:
        return super().__new__(cls, float(value))

    def __init__(
        self,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> None:
        require_finite(float(self), type(self).__name__)
        require_version(schema_version, f"{type(self).__name__}.schema_version")
        object.__setattr__(self, "schema_version", schema_version)
        object.__setattr__(self, "created_at", created_at or resolve_clock(clock).now())
        object.__setattr__(
            self,
            "uuid",
            uuid_value
            or resolve_id_generator(id_generator).generate(type(self).__name__, float(self)),
        )

    def __setattr__(self, name: str, value: object) -> None:
        """Prevent mutation of technical identity after construction."""
        raise AttributeError(f"{type(self).__name__} is immutable")

    def __copy__(self) -> Self:
        return self

    def __deepcopy__(self, memo: dict[int, object]) -> Self:
        del memo
        return self

    def to_dict(self) -> dict[str, Any]:
        """Serialize the value object into a dictionary."""
        return {
            "value": float(self),
            "schema_version": self.schema_version,
            "created_at": self.created_at,
            "uuid": self.uuid,
        }

    @classmethod
    @integrity_deserializer
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
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> Self:
        numeric_value = require_unit_interval(value, "confidence")
        return super().__new__(
            cls, numeric_value, schema_version, created_at, uuid_value, clock, id_generator
        )


class Probability(_DomainValue):
    """Probability score restricted to the [0.0, 1.0] interval."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> Self:
        numeric_value = require_unit_interval(value, "probability")
        return super().__new__(
            cls, numeric_value, schema_version, created_at, uuid_value, clock, id_generator
        )


class RiskScore(_DomainValue):
    """Risk score restricted to the [0.0, 1.0] interval."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> Self:
        numeric_value = require_unit_interval(value, "risk_score")
        return super().__new__(
            cls, numeric_value, schema_version, created_at, uuid_value, clock, id_generator
        )


class Price(_DomainValue):
    """Price value object restricted to non-negative values."""

    def __new__(
        cls,
        value: float,
        schema_version: int = 1,
        created_at: str = "",
        uuid_value: str = "",
        clock: ClockProtocol | None = None,
        id_generator: IdGeneratorProtocol | None = None,
    ) -> Self:
        numeric_value = require_non_negative(value, "price")
        return super().__new__(
            cls, numeric_value, schema_version, created_at, uuid_value, clock, id_generator
        )
