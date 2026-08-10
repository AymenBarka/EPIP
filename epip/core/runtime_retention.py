"""Transparent runtime adoption of institutional retention policies."""

from __future__ import annotations

from collections.abc import Iterable, Iterator, Mapping
from dataclasses import dataclass
from enum import Enum
from types import MappingProxyType
from typing import Any

from epip.core.retention import (
    MEMORY_RETENTION_CONTRACTS,
    MemoryRetentionContract,
    RetentionManager,
)


class RetentionAdoptionMode(str, Enum):
    """How an existing runtime participates in retention management."""

    TRANSPARENT_ADAPTER = "transparent_adapter"
    NATIVE = "native"


@dataclass(frozen=True, slots=True)
class RuntimeRetentionAdoption:
    """Immutable declaration of effective runtime adoption."""

    component: str
    contract: MemoryRetentionContract
    mode: RetentionAdoptionMode
    migrated: bool
    preserves_default: bool

    def __post_init__(self) -> None:
        if self.component != self.contract.component:
            raise ValueError("adoption component must match its retention contract")
        if not self.migrated:
            raise ValueError("registered runtime adoption must be migrated")
        if not self.preserves_default:
            raise ValueError("runtime adoption must preserve the existing default")


class RuntimeRetentionRegistry(Mapping[str, RuntimeRetentionAdoption]):
    """Immutable registry and automated migration audit."""

    def __init__(self, adoptions: Iterable[RuntimeRetentionAdoption]) -> None:
        items = tuple(adoptions)
        values = {item.component: item for item in items}
        if len(values) != len(items):
            raise ValueError("runtime adoption component names must be unique")
        self._adoptions: Mapping[str, RuntimeRetentionAdoption] = MappingProxyType(values)

    def __getitem__(self, key: str) -> RuntimeRetentionAdoption:
        return self._adoptions[key]

    def __iter__(self) -> Iterator[str]:
        return iter(self._adoptions)

    def __len__(self) -> int:
        return len(self._adoptions)

    def declared(self) -> tuple[RuntimeRetentionAdoption, ...]:
        return tuple(self._adoptions[name] for name in sorted(self._adoptions))

    def audit(self) -> tuple[str, ...]:
        errors: list[str] = []
        expected = set(MEMORY_RETENTION_CONTRACTS)
        for name in sorted(expected - set(self._adoptions)):
            errors.append(f"runtime structure not migrated: {name}")
        for name in sorted(set(self._adoptions) - expected):
            errors.append(f"runtime adoption has no retention policy: {name}")
        for name, adoption in sorted(self._adoptions.items()):
            if adoption.contract != MEMORY_RETENTION_CONTRACTS[name]:
                errors.append(f"incoherent runtime adoption: {name}")
        return tuple(errors)


class RuntimeRetentionAdapter[T, K]:
    """Transparent component facade with deterministic retained state."""

    def __init__(
        self,
        component: T,
        adoption: RuntimeRetentionAdoption,
    ) -> None:
        self._component = component
        self._adoption = adoption
        self._retention = RetentionManager[K, Any](adoption.contract)

    @property
    def component(self) -> T:
        """Return the unchanged wrapped runtime component."""

        return self._component

    @property
    def runtime_retention(self) -> RuntimeRetentionAdoption:
        return self._adoption

    @property
    def retention_manager(self) -> RetentionManager[K, Any]:
        return self._retention

    def retain(self, key: K, value: Any, *, timestamp: float | None = None) -> None:
        """Retain runtime data according to the effective contract."""

        self._retention.put(key, value, timestamp=timestamp)

    def retained_snapshot(self) -> tuple[tuple[K, Any], ...]:
        return self._retention.snapshot()

    def clear_retained(self) -> int:
        return self._retention.clear()

    def __getattr__(self, name: str) -> Any:
        """Delegate existing behaviour without altering the wrapped API."""

        return getattr(self._component, name)


def _qualified_name(component: object) -> str:
    component_type = type(component)
    return f"{component_type.__module__}.{component_type.__qualname__}"


def adopt_runtime_retention[T, K](
    component: T,
    *,
    component_name: str | None = None,
    contract: MemoryRetentionContract | None = None,
) -> RuntimeRetentionAdapter[T, K]:
    """Explicitly and reversibly adopt retention for an existing runtime."""

    name = component_name or _qualified_name(component)
    effective = contract or MEMORY_RETENTION_CONTRACTS[name]
    if effective.component != name:
        raise ValueError("explicit retention contract does not match component")
    adoption = RUNTIME_RETENTION_ADOPTIONS[name]
    if adoption.contract != effective:
        adoption = RuntimeRetentionAdoption(
            component=name,
            contract=effective,
            mode=RetentionAdoptionMode.TRANSPARENT_ADAPTER,
            migrated=True,
            preserves_default=True,
        )
    return RuntimeRetentionAdapter(component, adoption)


RUNTIME_RETENTION_ADOPTIONS = RuntimeRetentionRegistry(
    RuntimeRetentionAdoption(
        component=contract.component,
        contract=contract,
        mode=RetentionAdoptionMode.TRANSPARENT_ADAPTER,
        migrated=True,
        preserves_default=True,
    )
    for contract in MEMORY_RETENTION_CONTRACTS.values()
)


__all__ = [
    "RUNTIME_RETENTION_ADOPTIONS",
    "RetentionAdoptionMode",
    "RuntimeRetentionAdapter",
    "RuntimeRetentionAdoption",
    "RuntimeRetentionRegistry",
    "adopt_runtime_retention",
]
