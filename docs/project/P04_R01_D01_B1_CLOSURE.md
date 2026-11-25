# P04-R01-D01-B1 — First Development Tick Batch (Implementation)

Status: **D01-B1 — ACQUISITION IN PROGRESS — PARTIAL BATCH**

Window `D01-B1-EURUSD-2018-01` is **AUTHORIZED FOR OWNER-RUN ACQUISITION**
(section 12); the eleven other windows remain **CLOSED**. No historical data
has been acquired yet.

D01-B1 implements, offline, the tooling for the first development batch frozen
in
[P04-R01-Q00-G00](P04_R01_Q00_G00_QUANTITATIVE_VALIDATION_PROTOCOL_RECONCILIATION.md):
Dukascopy BID/ASK ticks for EURUSD and XAUUSD from
`2018-01-01T00:00:00Z` (inclusive) to `2018-07-01T00:00:00Z` (exclusive),
H1/H4 derived from ticks, and the provider H1 cross-check. No historical data
was acquired during implementation. Gates are opened only by separate owner
authorizations (sections 11 and 12). D01-B1 is not
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
| D00 synthetic content | Unchanged: canonical SHA-256 and row counts pinned by test (platform-independent) |
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
& $py -m research.datasets batch-plan --batch D01-B1
& $py -m research.datasets acquire --window D01-B1-EURUSD-2018-01 --dry-run

# One instrument-month acquisition with provider-terms confirmation (gated)
& $py -m research.datasets acquire --window D01-B1-EURUSD-2018-01 --data-root data --confirm-provider-terms

# Resume after an abort or a ceiling: rerun the same command (gated);
# verified files are skipped and never overwritten

# Build, registry verify, fresh-root reproduction, quality, manifest export
& $py -m research.datasets build --window D01-B1-EURUSD-2018-01 --data-root data
& $py -m research.datasets registry verify DATASET_ID --data-root data
& $py -m research.datasets reproduce --window D01-B1-EURUSD-2018-01 --data-root data --fresh-root data-fresh-EURUSD-2018-01
& $py -m research.datasets batch-quality --batch D01-B1 --data-root data
& $py -m research.datasets export-manifests --window D01-B1-EURUSD-2018-01 --data-root data
```

## 10. Known risks

- Provider throttling (HTTP 503) may lengthen runs; the run and daily ceilings
  bound exposure, and resume is idempotent.
- Holiday hours (2018-01-01, 2018-03-30) will likely need owner decisions;
  Dukascopy does not publish machine-readable 2018 holiday hours.
- The XAUUSD Sunday reopen rule is new in v2; if observed data contradicts
  it, a populated hour is kept as populated (the calendar only classifies
  empty hours), and a calendar amendment is required before any rule change.
- Dataset identifiers include the compressed-content digest, which depends on
  the zlib implementation: the synthetic D00 H4 identifiers differ between
  zlib 1.3.1 (owner's Windows, Python 3.13.1) and zlib-ng (Linux build,
  Python 3.13.18) while canonical SHA-256 values are identical. The first
  version of the D00 regression test pinned zlib-ng identifiers and failed on
  Windows and in Research CI at `30094634`; it now pins canonical content. This D00 property is unchanged by
  D01-B1; D00 identifiers (and D01 identifiers) are reproducible only with
  the same zlib implementation. Changing the identity contract requires a
  separate owner authorization. D01 reproduction and manifest commits must
  use the owner's Windows environment.
- Byte estimates derive from one D00 month (2012-03); 2018 volumes may
  differ, and the 100 MB per-run ceiling then splits a month across runs.

## 11. Gate opening rule

Opening acquisition requires a separate owner authorization that names the
windows to open (one instrument-month at a time or the twelve), confirms the
Dukascopy terms, and changes `acquisition_open` for those windows in
`research/datasets/batches.py` in a governed commit. Acquisition, owner
decisions, quality gates, fresh-root reproduction, manifest commit and D01-B1
closure follow under that authorization. D01-P, D01-B2+, Q00-I00 and all
downstream steps remain NOT AUTHORIZED.

## 12. First acquisition window authorization

Authorized by the owner's P04-R01-D01-B1 first acquisition window
authorization (starting SHA `1f94a8024f75f9b16bf5c5a95d977624e7f0b387`),
amended by the owner's approval of acquisition locking (scope extended to
`research/datasets/acquisition.py` and `research/tests/**`). The
authorization opens one window and does not launch any download: the owner
confirms the Dukascopy terms and starts the acquisition on Windows.

### 12.1 Gate matrix

`OPEN_WINDOWS` in `research/datasets/batches.py` is the single source of
truth.

| Window | Gate | Planned requests |
| --- | --- | --- |
| D01-B1-EURUSD-2018-01 | **OPEN** (owner-run) | 554 |
| D01-B1-EURUSD-2018-02 | CLOSED | 482 |
| D01-B1-EURUSD-2018-03 | CLOSED | 528 |
| D01-B1-EURUSD-2018-04 | CLOSED | 509 |
| D01-B1-EURUSD-2018-05 | CLOSED | 554 |
| D01-B1-EURUSD-2018-06 | CLOSED | 503 |
| D01-B1-XAUUSD-2018-01 | CLOSED | 554 |
| D01-B1-XAUUSD-2018-02 | CLOSED | 482 |
| D01-B1-XAUUSD-2018-03 | CLOSED | 528 |
| D01-B1-XAUUSD-2018-04 | CLOSED | 509 |
| D01-B1-XAUUSD-2018-05 | CLOSED | 554 |
| D01-B1-XAUUSD-2018-06 | CLOSED | 503 |

### 12.2 Safety gates for the open window

| Gate | Evidence |
| --- | --- |
| Exact window | `2018-01-01T00:00:00Z` (1514764800000) to `2018-02-01T00:00:00Z` (1517443200000), end excluded |
| Planned requests | 554 (552 tick hours, 2 monthly candle files), ceiling 600 |
| Per run | 1500 requests, retries included; 100 MB |
| Spacing, timeout, retries | 1.0 s minimum; 30 s timeout (1–120 s); 4 retries with exponential backoff; consecutive-failure stop |
| Daily ceiling | 5000 requests per UTC day, persisted before each request |
| Resume | Journaled; verified raw files skipped; unverified files never overwritten |
| Concurrency | Exclusive global lock per data root and exclusive per-window lock (section 12.3) |
| Terms | `--confirm-provider-terms` required; without it the CLI refuses before creating a transport |
| Storage | Under `data/` (git-ignored); only metadata manifests are ever committed |

### 12.3 Acquisition locks

`run_acquisition` takes two lock files under `data/acquisition/locks/` before
any network request: `global.lock` (one acquisition per data root, protecting
the shared daily budget) and `<window_id>.lock`. Each is created atomically
with `O_CREAT | O_EXCL` (Windows and POSIX, standard library only) and
records `pid`, `host`, a random `token`, `window`, `acquired_utc`, and
`executable` (on Windows the venv `python.exe` is a launcher, so the
recorded `pid` is the interpreter process, its child). A held lock refuses the run before any transport call, journal
write or budget consumption. Locks are released in a `finally` block after
completion and after any exception (including Ctrl+C), and only if the file
still carries the process's own token; a foreign lock is never removed.
Dry runs and plans take no lock and write nothing; builds and quality checks
take no lock.

A lock left by a killed process, power failure or restart is never removed
automatically or because of its age. `inspect_locks` diagnoses each lock as
`ALIVE`, `NOT_RUNNING` (same host, process verified absent; Windows uses
`OpenProcess`/`GetExitCodeProcess`, never a signal) or `UNKNOWN` (other
host, unreadable file, unverifiable process). `release_stale_lock` removes a
lock only when the caller supplies its recorded token and the owner is
`NOT_RUNNING`; otherwise it fails closed.

Stale-lock recovery procedure (owner):

1. Confirm that no acquisition is running:
   `Get-CimInstance Win32_Process -Filter "Name='python.exe'" | Where-Object { $_.CommandLine -match 'research.datasets' } | Select-Object ProcessId, CommandLine`.
2. Inspect the locks:
   `& $py -c 'from pathlib import Path; from research.datasets.acquisition import inspect_locks; [print(i.name, i.state.value, i.owner) for i in inspect_locks(Path(''data''))]'`.
3. If a lock is `NOT_RUNNING`, release it with its recorded token:
   `& $py -c 'from pathlib import Path; from research.datasets.acquisition import release_stale_lock; release_stale_lock(Path(''data''), ''NAME'', ''TOKEN'')'`.
4. If a lock is `ALIVE` or `UNKNOWN` (for example a PID reused after a
   restart) and step 1 shows no acquisition process, the owner moves the
   file aside, keeping it as evidence:
   `Move-Item data\acquisition\locks\NAME.lock data\acquisition\locks\NAME.lock.stale-YYYYMMDD`.
5. Rerun the same acquisition command. The journal and verified raw files
   are preserved; a raw file without a journal record is refused, not
   overwritten, and is reported for an owner decision.

### 12.4 Owner-run Windows commands

Run from the repository root after the owner has confirmed the Dukascopy
terms for this batch. Claude does not run these commands.

```powershell
$py = ".\.venv313\Scripts\python.exe"
$w = "D01-B1-EURUSD-2018-01"

# 1. Dry run (no network, no file)
& $py -m research.datasets acquire --window $w --dry-run

# 2-3. Terms confirmation and acquisition (554 requests; about 2.2-3.7 h at the D00 observed throughput)
& $py -m research.datasets acquire --window $w --data-root data --confirm-provider-terms

# 4. Safe resume after throttling, a ceiling or an interruption: rerun the same command
& $py -m research.datasets acquire --window $w --data-root data --confirm-provider-terms

# 5. Build (refuses while any planned item is pending)
& $py -m research.datasets build --window $w --data-root data

# 6. Registry verification (repeat for each dataset id printed by build)
& $py -m research.datasets registry list --data-root data
& $py -m research.datasets registry verify DATASET_ID --data-root data

# 7. Fresh-root reproducibility (the fresh root must not exist or be empty)
& $py -m research.datasets reproduce --window $w --data-root data --fresh-root data-fresh-EURUSD-2018-01

# 8. Batch quality (exit 2 is expected while other windows are pending)
& $py -m research.datasets batch-quality --batch D01-B1 --data-root data

# 9. Manifest export for review (metadata only; not committed until reviewed)
& $py -m research.datasets export-manifests --window $w --data-root data
```

If Dukascopy throttles (HTTP 503), the run records the item, preserves the
journal and stops at the limits; resume with the same command. Never raise
the limits, shorten the spacing or run two acquisitions at once.

### 12.5 Quality review after acquisition

For the month: every planned item verified; unexpected empty hours
investigated; holiday closures (2018-01-01) only through an explicit,
sourced owner decision; corrupted or duplicate ticks stop the month; BID/ASK
consistency and H1/H4 derivation checked; EURUSD provider H1 cross-check
blocking; fresh-root rebuild on the same Windows environment with identical
canonical hashes and dataset identities; manifests exported for review. No
owner decision is added merely to make the gate pass, and no raw data is
committed.

### 12.6 Validation evidence

| Gate | Result |
| --- | --- |
| Black, Ruff (default and preview), MyPy strict | Pass |
| Research tests | 301 passed twice (276 existing nodes preserved, 25 new lock and gate nodes) |
| Genuine concurrent processes | Same window, other window on the same root, six-process atomic race (exactly one winner) |
| Coverage `research/datasets` / `research/elliott_causal` | ≥ 99.9 % (only the Windows-only `WinDLL` loader is excluded) / 100 % |
| Production regression | 3127 passed |
| Compliance inventory / digest | 612 / `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |
| Network | None |

Remaining NOT AUTHORIZED: the eleven other D01-B1 windows, D01-P, D01-B2+,
Q00-I00 and all later Q00 milestones, C00, P04-F02/F03/F04, P05, demo and
live trading.
