# Developer Guide

## Contribution principles

Preserve stable public APIs and dependency direction. Add behavior to the owning bounded context.
Do not duplicate Decision, sizing, or execution logic. Prefer immutable dataclasses, pure domain
services, explicit exceptions, protocols at external boundaries, `RLock` for engine state, and
logging instead of `print`.

## Repository structure

- `epip/<domain>/`: public API, engine, models, protocols, domain services, events, metrics,
  serialization, history, and graph.
- `tests/<domain>/`: unit and integration tests.
- `tests/benchmarks/`: manual performance benchmarks.
- `docs/architecture/`: module design documentation.
- `docs/adr/`: accepted architecture decisions.
- `docs/project/`: cross-project guides and release notes.
- `scripts/quality.py`: canonical local quality pipeline.

## Naming and coding rules

Use `PascalCase` for types, `snake_case` for functions/modules, and explicit domain names over
abbreviations. Public models are frozen dataclasses with slots when consistent with the module.
Use `StrEnum` for serialized states. Avoid hidden global state, nondeterministic identifiers in
snapshots, circular imports, wildcard APIs, direct broker access, and imports from downstream
modules.

## Testing

Cover the happy path, invalid inputs, state transitions, boundary values, serialization round trips,
history/version behavior, graph traversal, events, adapter protocols, thread-sensitive state, and
integration with the immediate upstream official object. Aggregate coverage must remain at least
95%; new public behavior should be covered directly rather than relying on aggregate headroom.

## Architecture review

Every engine-level feature needs an architecture document and ADR. Review public exports,
dependency direction, ownership of calculations, immutability, deterministic behavior, extension
points, operational failure modes, and backward compatibility.

## Git workflow

1. Start from current `develop` on a focused `feature/<domain>-engine` branch.
2. Keep unrelated changes out of the branch.
3. Run the complete quality pipeline.
4. Update documentation and changelog.
5. Stage only useful source, tests, and documentation; never caches, environments, coverage files,
   IDE settings, or generated reports.
6. Use a scoped Conventional Commit.
7. Push the feature branch for architect review; never merge before approval.

## Release workflow

After approval, merge with `--no-ff` into `develop`, rerun all quality gates, push `develop`, create
an annotated semantic-version tag, and push only that tag. Record the merge hash, quality outcome,
tag hash, and remote publication result. Never tag a failing build.
