# Evidence Engine

The EPIP-016 Evidence Engine is the deterministic infrastructure boundary for
decision evidence. It stores immutable facts and their provenance without
ranking, inference, recommendation, execution, or financial calculation.

## Components

- `EvidenceBuilder` normalizes payloads and dependencies and assigns a
  canonical content digest.
- `EvidenceValidator` enforces structural completeness and reference
  integrity.
- `EvidenceRegistry` owns deterministic indexes and lifecycle state.
- `EvidenceCollection` provides immutable filtered and grouped views.
- `EvidenceSnapshot` captures a versioned, byte-stable registry view.
- `EvidenceDiagnostics` reports inconsistencies without correcting data.
- `EvidenceEngine` is a functional facade: every operation returns a new
  instance.

## Architectural boundaries

The engine consumes only EPIP-016 decision-domain value objects and core
integrity primitives. It does not import lower-level trading engines and does
not reinterpret their calculations. Callers must supply identity, logical
time, version, source, confidence, quality, validity, and uncertainty
explicitly.

Registry indexes are derived from immutable entries. Ordering always uses the
stable evidence identifier. All digest material uses canonical JSON with
sorted keys and compact separators.

## Failure model

Invalid structure, duplicate identity, illegal lifecycle transitions, and
digest mismatches raise `RelationshipIntegrityError`. Unknown reference
resolution raises `KeyError`. Failed non-raising registration attempts are
retained in immutable audit statistics.
