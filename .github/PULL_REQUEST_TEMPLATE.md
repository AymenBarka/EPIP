## Summary

Describe the problem, solution, scope, and user-visible result.

## Architecture validation

- [ ] The owning bounded context is explicit.
- [ ] Dependencies follow `docs/project/DEPENDENCY_GRAPH.md`.
- [ ] No official calculation is duplicated or bypassed.
- [ ] External systems are behind protocols/adapters.
- [ ] Public models remain immutable and versioned where required.
- [ ] An ADR is added or updated for architecture decisions.

## Quality

- [ ] Black passes.
- [ ] Ruff passes.
- [ ] Strict MyPy passes.
- [ ] Pytest passes.
- [ ] Aggregate coverage is at least 95% and new behavior is directly tested.
- [ ] Relevant benchmarks were run or the performance impact is not applicable.

## Compatibility and documentation

- [ ] Stable public APIs remain backward compatible.
- [ ] Deprecations follow `docs/project/API_STABILITY.md`.
- [ ] Architecture, API, catalog, changelog, and release documentation are updated.
- [ ] Markdown links and Mermaid diagrams were validated.

## Delivery

- [ ] The branch is focused and contains no caches, environments, coverage, generated, or IDE files.
- [ ] Commit messages follow Conventional Commits.
- [ ] No merge or release tag is included in this PR branch.
