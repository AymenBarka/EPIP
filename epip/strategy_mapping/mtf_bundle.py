"""Typed multi-timeframe analytical source bundles."""

from __future__ import annotations

from dataclasses import dataclass

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import (
    FOUNDATION_SCHEMA_VERSION,
    digest,
    exact,
    instant,
    text,
    version,
)
from epip.strategy_mapping.instrument import InstrumentBinding
from epip.strategy_mapping.source_binding import AnalyticalSourceBinding
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.mtf import MultiTimeframeInputSet, TimeframeInput, TimeframeRole
from epip.strategy_runtime.provenance import ProvenanceManifest

_ROLE_ORDER = {TimeframeRole.PRIMARY: 0, TimeframeRole.HIGHER: 1, TimeframeRole.LOWER: 2}


@dataclass(frozen=True, slots=True)
class TimeframeAnalyticalFrame:
    frame_id: str
    frame: TimeframeInput
    sources: tuple[AnalyticalSourceBinding, ...]
    provenance_refs: tuple[str, ...]

    def __post_init__(self) -> None:
        exact(self.frame, TimeframeInput, "frame")
        if (
            type(self.sources) is not tuple
            or not self.sources
            or any(type(item) is not AnalyticalSourceBinding for item in self.sources)
        ):
            raise DataIntegrityError("sources must be a non-empty AnalyticalSourceBinding tuple")
        sources = tuple(sorted(self.sources, key=lambda item: item.canonical_key()))
        if len({item.source_binding_id for item in sources}) != len(sources):
            raise DataIntegrityError("frame source bindings must be unique")
        if any(item.timeframe != self.frame.timeframe or not item.closed for item in sources):
            raise DataIntegrityError("frame sources must be closed and timeframe coherent")
        object.__setattr__(self, "sources", sources)
        if type(self.provenance_refs) is not tuple or any(
            type(item) is not str or not item.strip() for item in self.provenance_refs
        ):
            raise DataIntegrityError("provenance_refs must be a text tuple")
        references = tuple(sorted(self.provenance_refs))
        expected = tuple(sorted(item.provenance_ref for item in sources))
        if len(set(references)) != len(references) or references != expected:
            raise DataIntegrityError("frame provenance refs must exactly match its sources")
        if tuple(sorted(self.frame.source_refs)) != expected:
            raise DataIntegrityError("P01 frame source refs must exactly match typed sources")
        object.__setattr__(self, "provenance_refs", references)
        if self.frame_id != digest(self, exclude=frozenset({"frame_id"})):
            raise DataIntegrityError("frame_id does not match canonical analytical frame")

    @classmethod
    def create(
        cls,
        frame: TimeframeInput,
        sources: tuple[AnalyticalSourceBinding, ...],
        provenance_refs: tuple[str, ...],
    ) -> TimeframeAnalyticalFrame:
        candidate = object.__new__(cls)
        values = (
            "",
            frame,
            tuple(sorted(sources, key=lambda item: item.canonical_key())),
            tuple(sorted(provenance_refs)),
        )
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        return cls(digest(candidate, exclude=frozenset({"frame_id"})), *values[1:])


@dataclass(frozen=True, slots=True)
class MultiTimeframeAnalyticalBundle:
    schema_version: str
    bundle_id: str
    instrument: InstrumentBinding
    coherence: MultiTimeframeInputSet
    frames: tuple[TimeframeAnalyticalFrame, ...]
    provenance_manifest_id: str

    def __post_init__(self) -> None:
        version(self.schema_version)
        exact(self.instrument, InstrumentBinding, "instrument")
        exact(self.coherence, MultiTimeframeInputSet, "coherence")
        if type(self.frames) is not tuple or any(
            type(item) is not TimeframeAnalyticalFrame for item in self.frames
        ):
            raise DataIntegrityError("frames must contain TimeframeAnalyticalFrame values")
        frames = tuple(
            sorted(
                self.frames, key=lambda item: (_ROLE_ORDER[item.frame.role], item.frame.timeframe)
            )
        )
        if not frames or len({item.frame.timeframe for item in frames}) != len(frames):
            raise DataIntegrityError("typed analytical frames must be non-empty and unique")
        if tuple((item.frame.timeframe, item.frame.role) for item in frames) != tuple(
            sorted(
                ((item.timeframe, item.role) for item in self.coherence.frames),
                key=lambda item: (_ROLE_ORDER[item[1]], item[0]),
            )
        ):
            raise DataIntegrityError("typed frames must exactly match P01 coherence frames")
        if any(
            source.instrument.binding_id != self.instrument.binding_id
            for item in frames
            for source in item.sources
        ):
            raise DataIntegrityError("MTF analytical sources must share one instrument")
        if any(
            instant(source.availability_timestamp) > instant(self.coherence.alignment_timestamp)
            or instant(source.as_of_timestamp) > instant(self.coherence.alignment_timestamp)
            for item in frames
            for source in item.sources
        ):
            raise DataIntegrityError("MTF source availability exceeds alignment time")
        object.__setattr__(self, "frames", frames)
        object.__setattr__(
            self,
            "provenance_manifest_id",
            text(self.provenance_manifest_id, "provenance_manifest_id"),
        )
        if self.bundle_id != digest(self, exclude=frozenset({"bundle_id"})):
            raise DataIntegrityError("bundle_id does not match canonical MTF analytical bundle")

    @classmethod
    def create(
        cls,
        instrument: InstrumentBinding,
        coherence: MultiTimeframeInputSet,
        frames: tuple[TimeframeAnalyticalFrame, ...],
        provenance_manifest_id: str,
    ) -> MultiTimeframeAnalyticalBundle:
        ordered = tuple(
            sorted(frames, key=lambda item: (_ROLE_ORDER[item.frame.role], item.frame.timeframe))
        )
        candidate = object.__new__(cls)
        values = (
            FOUNDATION_SCHEMA_VERSION,
            "",
            instrument,
            coherence,
            ordered,
            provenance_manifest_id,
        )
        for name, value in zip(cls.__dataclass_fields__, values, strict=True):
            object.__setattr__(candidate, name, value)
        return cls(values[0], digest(candidate, exclude=frozenset({"bundle_id"})), *values[2:])

    def validate_for(self, context: EvaluationContext, manifest: ProvenanceManifest) -> None:
        exact(context, EvaluationContext, "context")
        exact(manifest, ProvenanceManifest, "manifest")
        if self.provenance_manifest_id != manifest.manifest_id:
            raise DataIntegrityError("MTF bundle and provenance manifest differ")
        if self.instrument.instrument_id != context.instrument_id:
            raise DataIntegrityError("MTF bundle and evaluation instruments differ")
        if self.coherence.primary_timeframe != context.primary_timeframe or instant(
            self.coherence.alignment_timestamp
        ) > instant(context.evaluation_timestamp):
            raise DataIntegrityError("MTF bundle and evaluation context are temporally incoherent")
        for frame in self.frames:
            for source in frame.sources:
                source.validate_for(context, manifest)


__all__ = ["MultiTimeframeAnalyticalBundle", "TimeframeAnalyticalFrame"]
