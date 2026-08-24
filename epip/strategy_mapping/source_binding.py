"""Typed analytical source, availability, and revision contracts."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TypeAlias

from epip.context import MarketContextSnapshot
from epip.core import KernelResult
from epip.core.integrity import DataIntegrityError
from epip.decision import DecisionSnapshot
from epip.elliott import WaveSnapshot
from epip.fibonacci import FibonacciSnapshot
from epip.liquidity import LiquiditySnapshot
from epip.market_structure import MarketStructureSnapshot
from epip.strategy_mapping._base import (
    FOUNDATION_SCHEMA_VERSION,
    boolean,
    digest,
    exact,
    instant,
    non_negative_int,
    text,
    timestamp,
    version,
)
from epip.strategy_mapping.direction_policy import AnalyticalSourceKind
from epip.strategy_mapping.instrument import InstrumentBinding
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.provenance import ProvenanceManifest
from epip.swing import SwingSequence

AnalyticalPayload: TypeAlias = (
    SwingSequence
    | MarketStructureSnapshot
    | LiquiditySnapshot
    | FibonacciSnapshot
    | MarketContextSnapshot
    | WaveSnapshot
    | DecisionSnapshot
    | KernelResult
)

_PAYLOAD_TYPES: dict[AnalyticalSourceKind, type[object]] = {
    AnalyticalSourceKind.SWING: SwingSequence,
    AnalyticalSourceKind.MARKET_STRUCTURE: MarketStructureSnapshot,
    AnalyticalSourceKind.LIQUIDITY: LiquiditySnapshot,
    AnalyticalSourceKind.FIBONACCI: FibonacciSnapshot,
    AnalyticalSourceKind.MARKET_CONTEXT: MarketContextSnapshot,
    AnalyticalSourceKind.ELLIOTT: WaveSnapshot,
    AnalyticalSourceKind.DECISION: DecisionSnapshot,
    AnalyticalSourceKind.KERNEL: KernelResult,
}


@dataclass(frozen=True, slots=True, order=True)
class RevisionIdentity:
    source_series_id: str
    revision_id: str
    revision_ordinal: int
    supersedes_revision_id: str | None

    def __post_init__(self) -> None:
        object.__setattr__(
            self, "source_series_id", text(self.source_series_id, "source_series_id")
        )
        object.__setattr__(self, "revision_id", text(self.revision_id, "revision_id"))
        non_negative_int(self.revision_ordinal, "revision_ordinal")
        if self.supersedes_revision_id is not None:
            predecessor = text(self.supersedes_revision_id, "supersedes_revision_id")
            if predecessor == self.revision_id:
                raise DataIntegrityError("a revision cannot supersede itself")
            if self.revision_ordinal == 0:
                raise DataIntegrityError("ordinal zero cannot supersede a revision")


@dataclass(frozen=True, slots=True)
class AnalyticalSourceBinding:
    schema_version: str
    source_binding_id: str
    source_kind: AnalyticalSourceKind
    source_contract: str
    source_contract_version: str
    source_object_id: str
    instrument: InstrumentBinding
    timeframe: str
    observation_timestamp: str
    availability_timestamp: str
    as_of_timestamp: str
    revision: RevisionIdentity
    superseded_at: str | None
    closed: bool
    provenance_ref: str
    payload: AnalyticalPayload

    def __post_init__(self) -> None:
        version(self.schema_version)
        exact(self.source_kind, AnalyticalSourceKind, "source_kind")
        expected_type = _PAYLOAD_TYPES[self.source_kind]
        if type(self.payload) is not expected_type:
            raise DataIntegrityError("source kind and payload type differ")
        qualified = f"{expected_type.__module__}.{expected_type.__qualname__}"
        if self.source_contract != qualified:
            raise DataIntegrityError("source_contract does not identify the exact payload type")
        for name in (
            "source_contract_version",
            "source_object_id",
            "timeframe",
            "provenance_ref",
        ):
            object.__setattr__(self, name, text(getattr(self, name), name))
        exact(self.instrument, InstrumentBinding, "instrument")
        exact(self.revision, RevisionIdentity, "revision")
        for name in ("observation_timestamp", "availability_timestamp", "as_of_timestamp"):
            object.__setattr__(self, name, timestamp(getattr(self, name), name))
        if not (
            instant(self.observation_timestamp)
            <= instant(self.availability_timestamp)
            <= instant(self.as_of_timestamp)
        ):
            raise DataIntegrityError(
                "source timestamps violate observation/availability/as-of order"
            )
        if self.superseded_at is not None:
            superseded = timestamp(self.superseded_at, "superseded_at")
            if instant(superseded) <= instant(self.availability_timestamp):
                raise DataIntegrityError("superseded_at must follow availability")
            object.__setattr__(self, "superseded_at", superseded)
        if not boolean(self.closed, "closed"):
            raise DataIntegrityError("analytical sources must be closed")
        self._validate_payload_stream()
        if self.source_binding_id != digest(self, exclude=frozenset({"source_binding_id"})):
            raise DataIntegrityError("source_binding_id does not match canonical source binding")

    def _validate_payload_stream(self) -> None:
        symbol = getattr(self.payload, "symbol", None)
        if (
            symbol is not None
            and symbol != self.instrument.canonical_symbol
            and not any(item.symbol == symbol for item in self.instrument.aliases)
        ):
            raise DataIntegrityError("payload symbol is not admitted by instrument binding")
        payload_timeframe = getattr(self.payload, "timeframe", None)
        if payload_timeframe is not None and payload_timeframe != self.timeframe:
            raise DataIntegrityError("payload and source-binding timeframes differ")

    @classmethod
    def create(
        cls,
        *,
        source_kind: AnalyticalSourceKind,
        source_contract_version: str,
        source_object_id: str,
        instrument: InstrumentBinding,
        timeframe: str,
        observation_timestamp: str,
        availability_timestamp: str,
        as_of_timestamp: str,
        revision: RevisionIdentity,
        superseded_at: str | None,
        closed: bool,
        provenance_ref: str,
        payload: AnalyticalPayload,
    ) -> AnalyticalSourceBinding:
        exact(source_kind, AnalyticalSourceKind, "source_kind")
        payload_type = _PAYLOAD_TYPES[source_kind]
        if type(payload) is not payload_type:
            raise DataIntegrityError("source kind and payload type differ")
        contract = f"{payload_type.__module__}.{payload_type.__qualname__}"
        values = (
            FOUNDATION_SCHEMA_VERSION,
            "",
            source_kind,
            contract,
            source_contract_version,
            source_object_id,
            instrument,
            timeframe,
            timestamp(observation_timestamp, "observation_timestamp"),
            timestamp(availability_timestamp, "availability_timestamp"),
            timestamp(as_of_timestamp, "as_of_timestamp"),
            revision,
            None if superseded_at is None else timestamp(superseded_at, "superseded_at"),
            closed,
            provenance_ref,
            payload,
        )
        candidate = object.__new__(cls)
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        identity = digest(candidate, exclude=frozenset({"source_binding_id"}))
        return cls(values[0], identity, *values[2:])

    def validate_for(self, context: EvaluationContext, manifest: ProvenanceManifest) -> None:
        exact(context, EvaluationContext, "context")
        exact(manifest, ProvenanceManifest, "manifest")
        if context.instrument_id != self.instrument.instrument_id:
            raise DataIntegrityError("source instrument does not match evaluation context")
        if instant(self.as_of_timestamp) > instant(context.evaluation_timestamp) or instant(
            self.availability_timestamp
        ) > instant(context.evaluation_timestamp):
            raise DataIntegrityError("source binding contains future availability")
        if self.superseded_at is not None and instant(self.superseded_at) <= instant(
            self.as_of_timestamp
        ):
            raise DataIntegrityError("source revision was superseded at the as-of cutoff")
        if manifest.evaluation_id != context.evaluation_id:
            raise DataIntegrityError("manifest and evaluation context differ")
        sources = {item.source_object_id: item for item in manifest.sources}
        source = sources.get(self.provenance_ref)
        if source is None or self.provenance_ref != self.source_object_id:
            raise DataIntegrityError("source binding has dangling provenance")
        if (
            source.source_contract != self.source_contract
            or source.source_contract_version != self.source_contract_version
            or source.source_timestamp != self.observation_timestamp
        ):
            raise DataIntegrityError("source binding and provenance metadata differ")

    def canonical_key(self) -> tuple[str, str, str, str]:
        return (
            self.source_kind.value,
            self.source_contract,
            self.source_object_id,
            self.revision.revision_id,
        )


__all__ = ["AnalyticalPayload", "AnalyticalSourceBinding", "RevisionIdentity"]
