# Evidence Model

Evidence is an immutable, versioned record linking a stable identifier to a
category, source, structured payload, uncertainty measures, dependencies, and
decision metadata.

## Identity and provenance

- `evidence_id` is the stable business identity.
- `source` and `source_version` preserve provenance.
- `metadata` provides an explicit version, logical timestamp, and producer.
- `dependencies` contains stable evidence identifiers only.

No wall clock, random value, runtime address, or implicit identifier is used.

## Digests

The evidence content digest is SHA-256 over canonical immutable content with
the digest field excluded. A registry digest includes evidence content and
lifecycle state. A snapshot content digest includes its identity, version,
entries, and registry digest. Round-trip JSON restoration verifies both
registry and snapshot digests.

## Validation and diagnostics

Validation is structural. It checks required fields, versions, official
categories, self-dependencies, dependency resolution, and digest consistency.
It never evaluates trading meaning or financial quality.

Diagnostics report duplicate identifiers, unresolved references, unknown
categories, missing fields, and digest inconsistencies. Diagnostics never
mutate, infer, or repair evidence.
