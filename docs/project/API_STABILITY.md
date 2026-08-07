# API Stability Policy

## API classifications

### Public API

Symbols exported by a package-root `__all__`, documented engine methods, official snapshots,
`TradeDecision`, `PositionPlan`, `ExecutionSnapshot`, public events, protocols, configuration,
histories, and graphs are public. Public behavior includes constructor fields, enum values,
serialization shape, version semantics, documented exceptions, and dependency contracts.

### Internal API

Unexported analyzers, helper functions, private attributes, implementation modules, caches, and test
utilities are internal. Their use outside the owning package is unsupported and they may change in
any compatible release.

### Experimental API

An API is experimental only when its documentation and docstring explicitly say so. Experimental
symbols should not be re-exported from a stable package root unless clearly marked. They may evolve
between minor versions, but release notes must describe the change and migration.

## Compatibility guarantees

Within a supported major version, EPIP preserves documented imports, method contracts, enum values,
accepted serialized payloads, official object ownership, and dependency direction. Additive fields
must have safe defaults or versioned deserialization. Patch releases do not intentionally change
public behavior.

Compatibility does not cover private attributes, undocumented import paths, test helpers,
implementation timing, ordering not promised by documentation, third-party service behavior, or
unsupported versions.

## Deprecation policy

1. Publish the replacement and migration path.
2. Mark the old API as deprecated in documentation, docstring, changelog, and release notes.
3. Emit a targeted `DeprecationWarning` when practical without breaking deterministic behavior.
4. Preserve the API for at least one minor-release cycle and normally until the next major release.
5. Remove it only in a version permitted by semantic versioning.

Security fixes may require faster action. Any exception must be documented with impact, mitigation,
and supported upgrade path.

## Governance

Public API changes require direct tests, architecture review, updated object/event catalogs, and an
ADR when ownership or dependency boundaries change. The release checklist must confirm backward
compatibility before tagging.
