# Hypothesis Model

A hypothesis is an immutable, versioned interpretation supported by explicit
evidence references. It is not a decision or recommendation.

## Required structure

- stable hypothesis identifier and category;
- primary, supporting, and contradicting evidence references;
- explicit assumptions and invalidation conditions;
- confidence, quality, validity, and uncertainty values;
- versioned metadata and canonical content digest.

Collections sort hypotheses by identifier, reject duplicate identifiers, and
provide deterministic lookup by identifier, category, and evidence reference.
Equality remains the domain model's structural equality; registry lifecycle
state is stored separately and cannot alter business identity.

## Validation

Validation is structural only. It proves that references resolve, fields are
coherent, and the digest matches the content. It does not decide whether a
hypothesis is profitable, probable, or preferable.
