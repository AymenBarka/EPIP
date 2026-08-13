# Scenario Model

A scenario is an immutable grouping of registered hypotheses and evidence. It
describes a possible market interpretation without selecting an action.

## Required structure

- stable scenario identifier and category;
- one or more registered hypothesis references;
- optional parent scenarios and evidence references;
- explicit assumptions and invalidation conditions;
- confidence, quality, validity, and uncertainty values;
- versioned metadata and canonical content digest.

Scenario construction deliberately leaves ranking inputs empty. Programme C
does not rank scenarios and does not expose a preferred scenario. Parent
references must already be registered, which prevents forward-reference cycles
inside an immutable registry.

Scenario collections and registries expose deterministic lookup by identifier,
category, type, hypothesis, parent scenario, evidence, and digest.
