# Architecture Statistics

Generated for the EPIP `v1.4.0` governance milestone. Counts describe the current working tree and
use the methods below so future maintainers can reproduce them.

| Metric | Count | Method |
|---|---:|---|
| Completed EPIP modules | 14 | EPIP-001 through EPIP-014 |
| Public API symbols | 330 | Literal names in package-root `__all__` declarations |
| Immutable model classes | 257 | Python AST classes decorated with `@dataclass(frozen=True, ...)` under `epip/` |
| ADR files | 13 | Markdown files under `docs/adr/` (ADR-0002 through ADR-0014) |
| Missing ADR source files | 1 | ADR-0001 is referenced historically but absent |
| Benchmarks | 14 | `tests/benchmarks/benchmark_*.py` |
| Pytest tests | 205 | Tests collected by the latest successful full quality run |
| Test modules | 100 | `tests/**/test_*.py` |
| Documentation files | 58 | Repository Markdown files after the documentation landing page is added |
| Mermaid diagrams | 26 | Mermaid fenced blocks in repository Markdown files |
| Aggregate coverage | 97% | Latest successful `python scripts/quality.py` run |

## Public surface by domain

The 330-symbol public surface spans Core/runtime, Feature Store, Market Data, Replay, Swing,
Structure, Liquidity, Fibonacci, Market Context, Elliott, Decision, Risk, and Execution package
roots. The complete list and relationships are maintained in
[OBJECT_CATALOG.md](OBJECT_CATALOG.md).

## Interpretation

The high immutable-model count reflects EPIP's explicit typed domain vocabulary, event payloads,
snapshots, graph/history objects, and configuration values. Public symbol count is an API governance
metric, not a quality score: new exports increase compatibility obligations and should be justified
through review. ADR count intentionally excludes the missing ADR-0001 source rather than reporting
an invented record.

## Reproducibility

- Public APIs: parse each `epip/*/__init__.py` and count its literal `__all__` entries.
- Immutable models: parse `epip/**/*.py` with Python AST and count class decorators whose dataclass
  call sets `frozen=True`.
- Tests: use Pytest collection/full quality output; file count is not the test-case count.
- Documentation and diagrams: enumerate repository Markdown and count `mermaid` fenced blocks.
- Coverage: use the aggregate line coverage emitted by the canonical quality script.

Regenerate this report after a release that changes public exports, domain models, ADRs, tests,
benchmarks, or documentation.
