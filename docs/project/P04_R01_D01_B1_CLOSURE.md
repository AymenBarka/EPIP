# P04-R01-D01-B1 — First Development Tick Batch (Implementation)

Status: **D01-B1 — IMPLEMENTED / ACQUISITION AUTHORIZATION PENDING**

D01-B1 implements, offline, the tooling for the first development batch frozen
in
[P04-R01-Q00-G00](P04_R01_Q00_G00_QUANTITATIVE_VALIDATION_PROTOCOL_RECONCILIATION.md):
Dukascopy BID/ASK ticks for EURUSD and XAUUSD from
`2018-01-01T00:00:00Z` (inclusive) to `2018-07-01T00:00:00Z` (exclusive),
H1/H4 derived from ticks, and the provider H1 cross-check. No historical data
was acquired. Every D01-B1 acquisition gate is **CLOSED** in code; opening
them requires a separate owner authorization (section 10). D01-B1 is not
closed or frozen while acquisition, validation and reproducibility remain
pending.

## 1. Authority and scope

Authorized by the owner's P04-R01-D01-B1 implementation authorization,
starting SHA `3f4f0778e362c09cd43c9f29460967b265865858`. Offline
implementation and validation only: no network request, no download, no
real market-data payload, no D01-P, D01-B2, Q00-I00 or backtest.

| Path | Change |
| --- | --- |
| `research/datasets/calendar.py` | New: versioned session calendar `ny-1700-close/2`, holiday references |
| `research/datasets/batches.py` | New: D01-B1 batch registry (12 instrument-months), owner decisions |
| `research/datasets/batch_ops.py` | New: batch plan, monthly quality gates, fresh-root reproduction, manifest export |
| `research/datasets/acquisition.py` | Per-window calendar, weekend skipping, planned-request ceiling, acquisition gate, persistent daily budget |
| `research/datasets/build.py` | Calendar-versioned classification, owner decisions, single build provenance |
| `research/datasets/cli.py` | `batch-plan`, `batch-quality`, `reproduce`, `export-manifests`; gate check before any transport |
| `research/tests/test_d01_b1.py` | New: 24 offline synthetic-fixture test functions (25 nodes) |
| this record, `docs/project/ROADMAP.md` | Documentation |

Nothing changes under `epip/`, `tests/`, `research/elliott_causal/`,
`research/harness/`, `.github/workflows/`, `pyproject.toml` or
`requirements.txt`. No existing test node changes. No dependency is added.

## 2. Architecture

D01-B1 reuses the frozen D00 pipeline (plan → journal → acquisition → build →
registry → ledger) without changing any D00 contract:

- The D00 window registry (`AUTHORIZED_WINDOWS`) still contains only
  `A01-SAMPLE-2012-03`. D01 windows live in a separate registry
  (`research/datasets/batches.py`); `governed_window(id)` resolves either and
  refuses any other identifier. A collision check forbids a D01 identifier
  that already exists in D00.
- New `AuthorizedWindow` fields carry defaults equal to D00 behaviour
  (`calendar_version="ny-1700-close/1"`, `skip_scheduled_weekend=False`,
  `max_planned_requests=None`, `acquisition_open=True`), so the D00 window,
  its plan (244 requests) and its synthetic dataset identities are
  byte-identical; a regression test pins all eight D00 synthetic identities.
- Each D01-B1 window is one instrument-month: identifier
  `D01-B1-{SYMBOL}-2018-{MM}`, calendar `ny-1700-close/2`, weekend hours not
  requested, `max_planned_requests=600`, `max_requests=1500`,
  `max_bytes=100_000_000`, `acquisition_open=False`.
- Build provenance is one function (`build_provenance`) shared by the CLI and
  the batch tools, so rebuilding a window in the same root never produces a
  registry collision.

## 3. Calendar `ny-1700-close/2`

| Rule | Instruments | Source |
| --- | --- | --- |
| Weekend: Friday 17:00 → Sunday 17:00 America/New_York | All | D00 calendar v1 (frozen), Dukascopy observation in D00 |
| US DST: second Sunday of March 07:00 UTC → first Sunday of November 06:00 UTC | All | US Energy Policy Act 2005 (v1 rule) |
| Daily break Monday–Thursday 17:00–18:00 New York | XAUUSD | D00 calendar v1 |
| Sunday reopen hour 17:00–18:00 New York closed | XAUUSD | New in v2; metals reopen one hour after FX |
| 2018-01-01 New Year's Day | Reference only | Dukascopy notice of 2017-12-08 (hours not machine-readable) |
| 2018-03-30 Good Friday | Reference only | CME Globex 2018 holiday schedule (futures, not Dukascopy spot) |

Holidays are **references, never automatic closures**. An empty provider hour
on a holiday is classified `EMPTY_UNEXPLAINED`, annotated with an INFO
`HOLIDAY_REFERENCE` diagnostic, and blocks the month until a committed owner
decision declares it. Weekend hours skipped by the plan are recorded as
`EXPECTED_CLOSURE` with an INFO `SCHEDULED_CLOSURE_NOT_REQUESTED`
diagnostic. Calendar v1 (D00) is unchanged and remains selectable per window;
no D00 classification is rewritten.

## 4. Owner decisions

`research/datasets/batches.py` holds `OWNER_DECISIONS`, empty at this commit.
A decision names a window, a UTC hour, a kind, a source, a rationale and a
date:

| Kind | Applies only to | Effect |
| --- | --- | --- |
| `DECLARE_EXPECTED_CLOSURE` | An observed empty (`EMPTY_UNEXPLAINED`) hour | Hour becomes `EXPECTED_CLOSURE` |
| `DECLARE_MISSING` | A failed hour (404, throttled, transport error) | Hour becomes `MISSING`; affected bars are `INCOMPLETE` |
| `EXCLUDE_MONTH` | A whole window | Month is `EXCLUDED`; build refuses |

Decisions that do not match an observation, lie outside the window or the
plan, are duplicated, or belong to another window raise an integrity error.
Every applied decision is recorded as an INFO `OWNER_DECISION` diagnostic in
the manifest.

## 5. Acquisition limits

| Limit (Q00-G00) | Enforcement |
| --- | --- |
| ≤ 600 planned requests per instrument-month | `build_plan` refuses; maximum planned is 554 |
| ≤ 1500 requests per run | Run aborts at the ceiling; resume continues |
| ≤ 100 MB per run | Run aborts at the ceiling |
| ≥ 1 s between requests | Existing D00 pacing (1.0 s minimum) |
| ≤ 5000 requests per UTC day | `acquisition/daily_requests.jsonl`, appended before each request, persists across runs and restarts; a corrupted line stops the run |
| Bounded retries | Existing D00 retry policy (HTTP 503 and transport errors, capped) |
| Gate | `run_acquisition` and the CLI refuse a closed window before creating a transport |

## 6. Monthly quality gates

`batch-quality` evaluates each instrument-month in this order and reports one
status:

| Status | Condition |
| --- | --- |
| `STOPPED_CORRUPTED` | Any corrupted or duplicate tick payload; requires a policy amendment |
| `PENDING_ACQUISITION` | Any planned item not yet verified and not declared missing |
| `NEEDS_OWNER_DECISION` | Any undecided `EMPTY_UNEXPLAINED` hour (listed) |
| `BLOCKED_CROSSCHECK` | EURUSD derived H1 deviates from provider H1 |
| `EXCLUDED` | Owner excluded the month |
| `PASS` | Complete, decided, built; XAUUSD cross-check deviations are reported, not blocking |

`reproduce` copies the stored raw files and journal into an empty fresh root,
rebuilds, and requires identical dataset identities and canonical hashes.

## 7. Planned scope

| Month | Planned requests per instrument | Tick hours requested | Weekend hours not requested |
| --- | --- | --- | --- |
| 2018-01 | 554 | 552 | 192 |
| 2018-02 | 482 | 480 | 192 |
| 2018-03 | 528 | 526 | 218 |
| 2018-04 | 509 | 507 | 213 |
| 2018-05 | 554 | 552 | 192 |
| 2018-06 | 503 | 501 | 219 |

Totals: 12 windows, 6260 planned requests (two monthly candle files per
window). Estimates from D00 evidence: about 119.7 MB raw, about 215.5 MB
canonical gzip, 1.74 h minimum at one request per second, 25.0–41.7 h at the
D00 observed throughput. The 5000-request daily ceiling means the full batch
needs at least two UTC days; at the observed throughput it needs about
two to four days of run time.

Planned committed manifests (metadata only, after acquisition):
`research/datasets/manifests/<window_id>/<dataset_id>.json`, four per
window (ticks, H1, H4, provider candles). Raw and canonical payloads stay
under the git-ignored `data/` root and are never committed.

## 8. Validation evidence

| Gate | Result |
| --- | --- |
| Black, Ruff (default and preview), MyPy strict on `research/datasets research/elliott_causal research/tests` | Pass |
| Research tests | 276 passed (251 existing unchanged + 25 new), twice, identical |
| Coverage `research/datasets` | 100 % |
| Coverage `research/elliott_causal` | 100 % |
| D00 synthetic identities | Unchanged (pinned by test) |
| Production isolation | No import of `epip`, `research.elliott_causal` or `research.harness` from `research/datasets` |
| Production collection / compliance | 3127 / 612 unchanged (no production file touched) |
| Network | None; all tests use synthetic fixtures and a fake transport |

New tests cover monthly boundaries, February 2018/2020 and December →
January transitions, DST (2018-03-11), XAUUSD breaks, weekend skipping,
holiday references, planned-request, per-run and byte ceilings, HTTP 503
throttling with retry and resume, daily budget persistence and corruption,
raw-file immutability, duplicate and corrupted ticks, declared missing hours
and `INCOMPLETE` H4 bars, H1/H4 across weekends, EURUSD block and XAUUSD
report on cross-check deviations, fresh-root reproduction (identical and
mismatch), manifest export, registry tampering, ledger untouched, and the
closed gate in both the API and the CLI.

## 9. Windows commands

Run from the repository root with `$py = ".\.venv313\Scripts\python.exe"`.
Commands marked **gated** fail with `acquisition gate closed` until the gate
is opened by the authorization in section 10; none of the others makes a
network request.

```powershell
# Batch plan and per-window dry run (offline)
& $py -m research.datasets.cli batch-plan --batch D01-B1
& $py -m research.datasets.cli acquire --window D01-B1-EURUSD-2018-01 --dry-run

# One instrument-month acquisition with provider-terms confirmation (gated)
& $py -m research.datasets.cli acquire --window D01-B1-EURUSD-2018-01 --data-root data --confirm-provider-terms

# Resume after an abort or a ceiling: rerun the same command (gated);
# verified files are skipped and never overwritten

# Build, registry verify, fresh-root reproduction, quality, manifest export
& $py -m research.datasets.cli build --window D01-B1-EURUSD-2018-01 --data-root data
& $py -m research.datasets.cli registry verify <dataset_id> --data-root data
& $py -m research.datasets.cli reproduce --window D01-B1-EURUSD-2018-01 --data-root data --fresh-root data-fresh-EURUSD-2018-01
& $py -m research.datasets.cli batch-quality --batch D01-B1 --data-root data
& $py -m research.datasets.cli export-manifests --window D01-B1-EURUSD-2018-01 --data-root data
```

## 10. Known risks

- Provider throttling (HTTP 503) may lengthen runs; the run and daily ceilings
  bound exposure, and resume is idempotent.
- Holiday hours (2018-01-01, 2018-03-30) will likely need owner decisions;
  Dukascopy does not publish machine-readable 2018 holiday hours.
- The XAUUSD Sunday reopen rule is new in v2; if observed data contradicts
  it, a populated hour is kept as populated (the calendar only classifies
  empty hours), and a calendar amendment is required before any rule change.
- Byte estimates derive from one D00 month (2012-03); 2018 volumes may
  differ, and the 100 MB per-run ceiling then splits a month across runs.

## 11. Next authorization required

Opening acquisition requires a separate owner authorization that names the
windows to open (one instrument-month at a time or the twelve), confirms the
Dukascopy terms, and changes `acquisition_open` for those windows in
`research/datasets/batches.py` in a governed commit. Acquisition, owner
decisions, quality gates, fresh-root reproduction, manifest commit and D01-B1
closure follow under that authorization. D01-P, D01-B2+, Q00-I00 and all
downstream steps remain NOT AUTHORIZED.
