# EPIP

[![Python 3.13+](https://img.shields.io/badge/python-3.13%2B-3776AB?logo=python&logoColor=white)](https://www.python.org/)
[![Black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://black.readthedocs.io/)
[![Ruff](https://img.shields.io/badge/lint-ruff-D7FF64?logo=ruff&logoColor=black)](https://docs.astral.sh/ruff/)
[![MyPy strict](https://img.shields.io/badge/types-mypy%20strict-2A6DB2)](https://mypy.readthedocs.io/)
[![Coverage](https://img.shields.io/badge/coverage-97%25-brightgreen)](docs/project/QUALITY.md)
[![Release](https://img.shields.io/badge/release-v1.4.0-blue)](docs/project/releases/v1.4.0.md)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue)](LICENSE)
[![Quality](https://github.com/AymenBarka/EPIP/actions/workflows/quality.yml/badge.svg)](https://github.com/AymenBarka/EPIP/actions/workflows/quality.yml)
[![Documentation](https://github.com/AymenBarka/EPIP/actions/workflows/documentation.yml/badge.svg)](https://github.com/AymenBarka/EPIP/actions/workflows/documentation.yml)
[![Architecture](https://img.shields.io/badge/architecture-documented-success)](docs/project/ARCHITECTURE.md)

EPIP (Elliott Pattern Intelligence Platform) is a typed, event-driven Python framework for
building deterministic market-analysis and trading pipelines. It separates market data,
analytical engines, decisions, risk planning, and broker execution into versioned domain modules.

> EPIP is infrastructure for research and engineering. It does not provide financial advice or
> guarantee trading outcomes.

## Architecture

```mermaid
flowchart LR
    MD[Market Data] --> RP[Replay]
    RP --> SW[Swing]
    SW --> MS[Market Structure]
    MS --> LQ[Liquidity]
    LQ --> FB[Fibonacci]
    FB --> CT[Market Context]
    CT --> EW[Elliott Wave]
    EW --> DE[Decision]
    DE --> RK[Risk]
    RK --> EX[Execution]
    EX --> BA[Broker Adapter]
```

The framework applies domain-driven design, SOLID boundaries, immutable value objects, explicit
versioning, deterministic serialization, thread-safe engines, and EventBus-based integration.

## Completed modules

| EPIP | Module | Principal output |
|---|---|---|
| 001 | Core Domain | Domain values and contracts |
| 002 | Event Bus | Domain-event delivery |
| 003 | Feature Store | Versioned feature sets |
| 004 | Market Data | Normalized market data |
| 005 | Replay Engine | Deterministic replay sessions |
| 006 | Swing Engine | Swing sequences |
| 007 | Market Structure | Structure snapshots |
| 008 | Liquidity Engine | Liquidity snapshots |
| 009 | Fibonacci Engine | Fibonacci snapshots |
| 010 | Market Context | Market-context snapshots |
| 011 | Elliott Wave | Wave snapshots |
| 012 | Decision Engine | Trade decisions |
| 013 | Risk Engine | Position plans |
| 014 | Execution Engine | Execution snapshots |

## Installation

EPIP requires Python 3.13 or newer.

```bash
python -m venv .venv
python -m pip install -e ".[dev]"
```

Activate the virtual environment using the command appropriate to your shell.

## Quick start

Public engines use explicit configuration and the shared EventBus. Downstream modules consume
immutable outputs rather than recomputing upstream work.

```python
from epip.core import EventBus
from epip.execution import ExecutionEngine

bus = EventBus()
execution = ExecutionEngine(event_bus=bus)

# PositionPlan is produced by RiskEngine.
# snapshot = execution.execute(position_plan, timestamp="2026-01-01T00:00:00Z")
```

See [API Guide](docs/project/API_GUIDE.md) and [Pipeline](docs/project/PIPELINE.md) for complete
integration guidance.

## Development and quality

```bash
python scripts/quality.py
```

Every change must pass Black, Ruff, strict MyPy, Pytest, and at least 95% aggregate coverage.
Benchmarks live in `tests/benchmarks/`. Read the [Developer Guide](docs/project/DEVELOPER_GUIDE.md)
and [Quality Guide](docs/project/QUALITY.md) before contributing.

## Documentation

- [Project overview](docs/project/PROJECT_OVERVIEW.md)
- [Architecture](docs/project/ARCHITECTURE.md)
- [Architecture decisions](docs/project/DECISIONS.md)
- [Dependency graph](docs/project/DEPENDENCY_GRAPH.md)
- [Modules](docs/project/MODULES.md)
- [Trading pipeline](docs/project/PIPELINE.md)
- [API guide](docs/project/API_GUIDE.md)
- [Glossary](docs/project/GLOSSARY.md)
- [Object catalog](docs/project/OBJECT_CATALOG.md)
- [Event catalog](docs/project/EVENT_CATALOG.md)
- [Architecture principles](docs/project/ARCHITECTURE_PRINCIPLES.md)
- [API stability](docs/project/API_STABILITY.md)
- [Release policy](docs/project/RELEASE_POLICY.md)
- [Architecture statistics](docs/project/ARCHITECTURE_STATISTICS.md)
- [Roadmap](docs/project/ROADMAP.md)
- [Release summary](docs/project/CHANGELOG_SUMMARY.md)
- [FAQ](docs/project/FAQ.md)
- [Future vision](docs/project/FUTURE.md)

Module-level design documents and architecture decisions are available under
`docs/architecture/` and `docs/adr/`.

## Releases

The current framework milestone is `v1.4.0`, containing the pipeline through execution. Release
notes are maintained in [`docs/project/releases/`](docs/project/releases/).

## Roadmap

The next planned modules are Portfolio (`v1.5.0`), Strategy (`v1.6.0`), Monitoring and
Observability (`v1.7.0`), and AI (`v2.0.0`).

## Contributing

Use a focused feature branch, preserve public API compatibility, add tests and documentation, run
all quality gates, and request architectural review before merging.

## License

EPIP is licensed under the [Apache License 2.0](LICENSE).
