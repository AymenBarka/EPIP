"""Plugin-scoped execution context for EPIP plugins."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from epip.core.registry import Registry

from epip.core.context import MarketContext
from epip.core.event_bus import EventBus
from epip.core.identity import (
    ClockProtocol,
    IdGeneratorProtocol,
    resolve_clock,
    resolve_id_generator,
)


@dataclass(frozen=True, slots=True)
class PluginContext:
    """Immutable context passed to plugins by the kernel."""

    market_context: MarketContext
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False)
    event_bus: EventBus = field(default_factory=EventBus, compare=False)
    registry: Registry | None = field(default=None, compare=False)
    clock: ClockProtocol | None = field(default=None, compare=False)
    id_generator: IdGeneratorProtocol | None = field(default=None, compare=False)

    def __post_init__(self) -> None:
        """Normalize the metadata into an immutable mapping."""
        from epip.core.registry import Registry

        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
        object.__setattr__(self, "registry", self.registry or Registry())
        object.__setattr__(self, "clock", resolve_clock(self.clock))
        object.__setattr__(self, "id_generator", resolve_id_generator(self.id_generator))
