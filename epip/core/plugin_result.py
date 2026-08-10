"""Immutable plugin execution result object."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import Any

from epip.core.evidence import Evidence


@dataclass(frozen=True, slots=True)
class PluginResult:
    """Immutable outcome of a single plugin execution."""

    plugin: str
    execution_time: float = field(compare=False)
    success: bool
    errors: tuple[str, ...] = field(default_factory=tuple)
    warnings: tuple[str, ...] = field(default_factory=tuple)
    generated_evidence: tuple[Evidence, ...] = field(default_factory=tuple)
    metadata: Mapping[str, Any] = field(default_factory=dict, compare=False)

    def __post_init__(self) -> None:
        """Normalize tuple and mapping fields for immutability."""
        object.__setattr__(self, "errors", tuple(self.errors))
        object.__setattr__(self, "warnings", tuple(self.warnings))
        object.__setattr__(self, "generated_evidence", tuple(self.generated_evidence))
        object.__setattr__(self, "metadata", MappingProxyType(dict(self.metadata)))
