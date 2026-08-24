"""Canonical immutable instrument identity contracts."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import FOUNDATION_SCHEMA_VERSION, digest, text, version


@dataclass(frozen=True, slots=True, order=True)
class InstrumentAlias:
    provider_id: str
    symbol: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_id", text(self.provider_id, "provider_id"))
        object.__setattr__(self, "symbol", text(self.symbol, "symbol"))


@dataclass(frozen=True, slots=True)
class InstrumentBinding:
    schema_version: str
    binding_id: str
    instrument_id: str
    canonical_symbol: str
    aliases: tuple[InstrumentAlias, ...]
    binding_version: str

    def __post_init__(self) -> None:
        version(self.schema_version)
        for name in ("instrument_id", "canonical_symbol", "binding_version"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        if type(self.aliases) is not tuple or any(
            type(item) is not InstrumentAlias for item in self.aliases
        ):
            raise DataIntegrityError("aliases must be a tuple of InstrumentAlias")
        aliases = tuple(sorted(self.aliases))
        if len(set(aliases)) != len(aliases):
            raise DataIntegrityError("instrument aliases must be unique")
        providers = tuple(item.provider_id for item in aliases)
        if len(set(providers)) != len(providers):
            raise DataIntegrityError("one provider must not map conflicting symbols")
        object.__setattr__(self, "aliases", aliases)
        if self.binding_id != digest(self, exclude=frozenset({"binding_id"})):
            raise DataIntegrityError("binding_id does not match canonical instrument binding")

    @classmethod
    def create(
        cls,
        instrument_id: str,
        canonical_symbol: str,
        aliases: tuple[InstrumentAlias, ...],
        binding_version: str,
    ) -> InstrumentBinding:
        if type(aliases) is not tuple or any(type(item) is not InstrumentAlias for item in aliases):
            raise DataIntegrityError("aliases must be a tuple of InstrumentAlias")
        candidate = object.__new__(cls)
        values = (
            FOUNDATION_SCHEMA_VERSION,
            "",
            instrument_id,
            canonical_symbol,
            tuple(sorted(aliases)),
            binding_version,
        )
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        return cls(
            schema_version=FOUNDATION_SCHEMA_VERSION,
            binding_id=digest(candidate, exclude=frozenset({"binding_id"})),
            instrument_id=instrument_id,
            canonical_symbol=canonical_symbol,
            aliases=tuple(sorted(aliases)),
            binding_version=binding_version,
        )

    def admits(self, provider_id: str | None, symbol: str) -> bool:
        text(symbol, "symbol")
        if provider_id is None:
            return symbol == self.canonical_symbol
        key = (text(provider_id, "provider_id"), symbol)
        return any((item.provider_id, item.symbol) == key for item in self.aliases)


__all__ = ["InstrumentAlias", "InstrumentBinding"]
