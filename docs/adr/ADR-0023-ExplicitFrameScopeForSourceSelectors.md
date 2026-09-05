# ADR-0023: Explicit Frame Scope for Source Selectors

## Status

Accepted

## Context

P02-F09 found that `SourceSelector` identifies a source kind, contract, selector kind, and exact
rule but not a timeframe role. A typed bundle can legally contain matching sources in several
roles. Treating ordinary selectors as implicitly PRIMARY or implicitly all-frame would put
strategy semantics into generic adapter control flow and alter candidate and evidence identities.

## Decision

`SourceSelector` will gain mandatory `frame_roles: tuple[TimeframeRole, ...]`. The tuple is non-empty,
contains exact unique roles, and canonicalizes to PRIMARY, HIGHER, LOWER. There is no default or
wildcard. One selector may intentionally admit several roles; P04 must make that choice explicitly.

P02 resolves frames by declared role, then timeframe, then the existing source canonical key. F06
per-frame direction uses the same resolution rule narrowed by its explicit active frame; the reused
direction selector must admit that role. Candidate normalization remains unordered, while F08
ranked output remains semantic and untouched.

The scope participates in serialization, reconstruction, equality, hashing, selector canonical
keys, and semantic-profile fingerprints. It adds no executable identity or rule taxonomy.

## Consequences

Existing serialized selectors without the field fail closed. P02-F11 must migrate each constructor
with an explicit governed role tuple and prove deterministic resolution before P02-F09 can resume.
P01 and A07 remain frozen; P03 does not choose scope, P04 chooses concrete scopes, and P05 retains
all MTF aggregation semantics.
