# Contributing to EPIP

Thank you for helping improve EPIP. Contributions must preserve deterministic behavior, stable
public APIs, domain ownership, and the safety boundaries between Decision, Risk, and Execution.

## Before contributing

Read the [Developer Guide](docs/project/DEVELOPER_GUIDE.md),
[Architecture Principles](docs/project/ARCHITECTURE_PRINCIPLES.md),
[API Stability Policy](docs/project/API_STABILITY.md), and applicable ADRs in the
[decision index](docs/project/DECISIONS.md). Discuss large or breaking proposals before coding.

## Workflow

1. Fork or branch from current `develop`.
2. Use `feature/<name>`, `fix/<name>`, `docs/<name>`, or `chore/<name>`.
3. Keep each change focused and avoid unrelated formatting or refactoring.
4. Add or update tests and documentation with the implementation.
5. Run `python scripts/quality.py` and ensure coverage remains at least 95%.
6. Open a pull request using the repository checklist and respond to review feedback.

## Coding and architecture standards

- Target Python 3.13 and use the configured Black and Ruff rules.
- Pass strict MyPy; avoid untyped public interfaces.
- Prefer frozen dataclasses and deterministic serialization for published domain objects.
- Use protocols for external systems and `RLock` for stateful engine registries.
- Use logging, never `print`, in framework implementation.
- Depend only on Core, EventBus, and documented upstream contracts.
- Never duplicate another module's owned calculation or bypass official snapshots.
- Only Decision creates trade intent, only Risk sizes positions, and only Execution contacts broker
  adapters.

## Commits

Use Conventional Commits, for example `feat(risk): add sizing policy`, `fix(execution): reject
invalid transition`, or `docs(project): clarify API stability`. Write imperative, scoped messages.

## Testing and documentation

Cover success, failure, edge cases, transitions, serialization, history, graph, events, and the
immediate upstream integration. Update module architecture, ADRs, API documentation, changelog, and
release notes when contracts or architecture change. Benchmarks must describe their environment and
whether memory is measured or estimated.

## Review and releases

At least one maintainer review is required; architecture-sensitive changes require Chief Architect
approval. Maintainers merge approved branches into `develop` using `--no-ff`, rerun all gates, tag
annotated semantic versions, and publish release notes according to
[RELEASE_POLICY.md](docs/project/RELEASE_POLICY.md).

By participating, you agree to the [Code of Conduct](CODE_OF_CONDUCT.md) and security policy.
