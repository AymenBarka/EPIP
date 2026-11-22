# P04-R01-G00 — Research Governance and Causal Elliott Readiness

Status: **CLOSED / FROZEN** upon publication, subject to exact-final-commit
publication gates

Scope: research governance and authorization boundaries only; no
implementation, no data acquisition, no backtest

## 1. Status and authority

P04-R01-G00 governs the research program that must precede any P04-F02
authorization. It reconciles the owner's audit of 2026-11-22 with
[P04-R00](P04_R00_ELLIOTT_FIBONACCI_SETUP_RECONCILIATION.md),
[P04-F01-R01](P04_F01_R01_ELLIOTT_FIBONACCI_WAVE3_SETUP_QUALIFICATION_CONTRACT.md),
[P04-F02-R01](P04_F02_R01_GEOMETRY_A07_RR_OWNERSHIP_RECONCILIATION.md), the
[P02-R05 closure](P02_R05_IMPLEMENTATION_CLOSURE.md), and
[ADR-0011](../adr/ADR-0011-ElliottWaveEngine.md).

This record:

- freezes the research sequence G00 → D00 → E00 → Q00 → C00;
- authorizes **P04-R01-D00 only**, within the boundary of section 19;
- does not authorize E00, Q00, C00, P04-F02, P04-F03, P04-F04, or P05;
- changes no production code, frozen contract, identity, or fingerprint.

The owner approved five decisions that bind every R01 milestone:

| ID | Decision |
| --- | --- |
| D1 | Historical data lives in repository-root `data/`, excluded from Git, reproducible through versioned manifests and SHA-256 checksums. |
| D2 | Data acquisition runs as Python scripts executed locally on Windows. No provider is preselected. |
| D3 | GBPUSD and USDJPY are `UNVERIFIED — NOT ATTESTED VIRGIN` until audited; absence of evidence is not evidence of virginity. |
| D4 | A dedicated Research CI gate is a future requirement; G00 defines its contract only. |
| D5 | The ten historical untracked documents are preserved untouched; an external archive destination is proposed. |

## 2. Starting repository baseline

Measured before this publication:

| Item | Value |
| --- | --- |
| Branch | `develop` |
| HEAD and `origin/develop` | `01c38b55cd30fd425635448f96b2e3d34b34eca6` (0 ahead, 0 behind) |
| Tracked modifications | none |
| Pytest collection | 3127 |
| Compliance inventory | 612 |
| Compliance digest | `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |
| Remote gates on `01c38b55` | Quality 45020535728, CodeQL 45020535563, Documentation 45020535655: all success |
| P02-R05 | CLOSED / FROZEN |
| P04-F00 / P04-F01 | CLOSED / FROZEN |
| P04-F02 | READY FOR AUTHORIZATION REVIEW before this record |

Untracked and preserved: the ten historical documents of section 7.4,
`.pytest-local-runtime/`, and audit artifacts under `research/`.

## 3. Research mission and strategic objective

EPIP targets an autonomous, causal, reproducible, and robust algorithmic trading
engine, with EPIP Python as the sole decision core and MetaTrader 5 as a future
backtesting and execution platform. A SaaS product is not a current objective
and must not influence engine architecture.

Three questions are kept separate throughout R01:

1. **Contract conformance:** do producers emit the facts the frozen contracts
   define?
2. **Causality and realism:** are those facts available on real data without
   future information, under realistic execution assumptions?
3. **Economic validity:** does a strategy show a robust edge after costs?

A strategy may satisfy question 1 and fail question 3. R01 never treats
technical conformance as evidence of profitability.

## 4. Confirmed Elliott producer limitations

The following behaviour of frozen production code at `01c38b55` is confirmed by
code inspection and by executed reproductions (section 16.3).

| ID | Location | Observed | Expected for real-data use | Severity |
| --- | --- | --- | --- | --- |
| E-1 | `epip/elliott/wave_detector.py` lines 13–15, 32–45 | Labels `swings[0..count]` of the **entire** swing history by position; newer swings never change the count | Counts over a recent window of significant swings | CRITICAL |
| E-2 | Consequence of E-1 with `epip/swing/config.py` lines 14–15 (2/2 window, no amplitude floor) | On 2,000 simulated H1 bars: 411 swings; a W1/W2 sequence exists on 2 bars only (12 and 13); 1,980 bars return the same frozen impulse | Recurring W1/W2 candidates across history | CRITICAL |
| E-5 | `epip/elliott/alternate_counter.py` lines 16–18 | Empty alternates holds only because fewer than three waves exist | Alternates produced by an actual count search | MAJOR |
| E-6 | `epip/elliott/wave_counter.py` lines 19–22 | Probability is a fixed formula, capped near 0.77 for two waves | Calibrated probability, or a declared uncalibrated score | MAJOR |
| E-7 | `epip/fibonacci/analyzer.py` lines 26–33 | Fibonacci direction follows market-structure trend, not W1 | Direction equal to W1 direction | MAJOR |
| E-8 | `epip/swing/pivot_window_detector.py` | Pivot carries the extreme's timestamp; its confirmation time (`right_bars` later) is not carried | Distinct extreme and availability timestamps | MAJOR |
| E-9 | `epip/elliott/degree_detector.py` | Degree is a timeframe lookup | Degree derived from amplitude and nesting | MINOR |

Verified as correct: window pivots are emitted only after `right_bars` closed
bars, and pivots do not repaint.

The Elliott unit suite remains valid for what it tests: it injects hand-built
swing sequences (for example `tests/elliott/helpers.py`, prices
`(1.0, 2.0, 1.5, 3.0, 2.5, 3.5)`), which never exercise a growing real stream.

## 5. Elliott/Fibonacci anchor contradiction

P04-R00 requires that Fibonacci retracement and extension anchors equal the W1
start and end prices exactly. The frozen producers cannot satisfy this jointly:

- the Elliott detector anchors W1 on the **first** two swings of history
  (E-1);
- the Fibonacci analyzer anchors on the **last** two confirmed swings
  (`epip/fibonacci/analyzer.py` lines 24–25).

With two swings, W1 exists but W2 does not. With three swings, Fibonacci is
anchored on W2. Except for degenerate equal prices, **no state satisfies F01
qualification by construction.**

Executed proof (section 16.3, E-4): engine-produced snapshots for
W1 100 → 120 and W2 → 107.64 make the frozen
`applicability.fibonacci-wave3` rule return `REJECTED`. Replacing only the
Fibonacci anchors by the W1 anchors makes the same rule return
`SUCCESS / applicable`. The hand-built F01 fixtures
(`tests/strategy_profiles/elliott_fibonacci/test_setup_rules.py` lines 76–123)
construct both snapshots with identical anchors, which explains why the
frozen suite passes.

**Reconciliation requirement R01-RQ1.** P04-R00 states that it resolved
analytical adequacy "without changing an analytical producer". That assumption
is falsified for real data. P04-R00 semantics are not rewritten here. Any
production producer change requires its own reconciliation milestone after C00
(section 22).

## 6. Frozen-contract preservation matrix

| Contract | R01 impact | Potential conflict | Treatment |
| --- | --- | --- | --- |
| P01 runtime contracts | none | none | unchanged |
| P02 and P02-R05 | none; R05 transport is consumed later by F02 | none | unchanged |
| P03 orchestration | none | none | unchanged |
| A07 E00–E09 | none | research R-multiples could be mistaken for decision RR | research R-multiples are statistical measures only; A07 E07 remains the exclusive RR, threshold, and zero-risk authority |
| P04-F00 configuration | values read as frozen | 300-second expiration and 0-second freshness versus realistic H1 entries | measured in E00 and Q00; any change goes through C00 decision B |
| P04-F01 qualification | rules, identities, and fingerprints invoked unchanged | mandatory empty alternates versus a genuine count search | frequency measured with and without alternates; P04-R00 already reserves alternates for a future profile version |
| P04-F01 confidence input | unchanged | calibrated probability required by confidence weighting | production formula kept and declared uncalibrated; calibration only with Q00 data |
| P04-R00 | semantics unchanged | producer-adequacy assumption falsified (R01-RQ1) | separate reconciliation after C00 |
| P04-F02-R01 | unchanged | none | geometry and RR ownership preserved |

Research prototypes must emit the existing frozen types (`WaveSnapshot`,
`ElliottAnalysis`, `FibonacciSnapshot`) through their public constructors.
They must not subclass, patch, or monkeypatch production code.

## 7. Historical dataset governance

### 7.1 Location and storage

- Datasets live under repository-root `data/`, which D00 adds to `.gitignore`.
- Raw provider files are immutable once fetched. Canonical files are derived
  deterministically from raw files.
- Only manifests, schemas, and acquisition code are versioned.

### 7.2 Scope

Initial instruments are EURUSD, GBPUSD, USDJPY, and XAUUSD, H1, with BID and
ASK sides when the provider offers them, from the first fully available month
to the last complete month. Lower timeframes are deferred until a milestone
requires intrabar ordering.

### 7.3 Canonical format

- UTC timestamps in ISO-8601, strictly increasing, no duplicates.
- Prices as integer points with a declared per-instrument scale.
- Zero-volume weekend bars removed; recurring session breaks (for example the
  daily metals break) declared, not treated as defects.
- Missing or incomplete periods declared as `MISSING` or `PARTIAL`, never
  interpolated.

### 7.4 Historical untracked documents (D5)

All ten files are preserved untouched. They predate A07 (modification times in
August 2026) and are superseded by `docs/project/ROADMAP.md`. None is
normative.

| Path | Purpose | Relationship |
| --- | --- | --- |
| `docs/architecture/EvidenceSemanticsAndDependencyResolution.md` | Evidence semantics draft | superseded by ADR-EPIP017-04 |
| `docs/project/A03_COMPATIBILITY_EVIDENCE.md` | A03 compatibility evidence | historical A03 working record |
| `docs/project/A03_CONFORMANCE_MATRIX.md` | A03 conformance matrix | historical A03 working record |
| `docs/project/A03_IMPLEMENTATION_MASTER_PLAN.md` | A03 implementation plan | superseded by tracked `A03_EXECUTION_PLAN_V2.md` |
| `docs/project/A04_EXECUTION_PLAN.md` | A04 execution plan | historical working record |
| `docs/project/CAPABILITY_MATRIX.md` | Capability snapshot | superseded by ROADMAP |
| `docs/project/CURRENT_ARCHITECTURE.md` | Architecture baseline snapshot | superseded by `ARCHITECTURE.md` and ADRs |
| `docs/project/MASTER_ROADMAP.md` | Early phase roadmap | superseded by ROADMAP |
| `docs/project/PRE_A07_RECONCILIATION.md` | Pre-A07 reconciliation | superseded by A07 completion evidence |
| `docs/project/PRODUCT_COMPLETION_MATRIX.md` | Product completion snapshot | superseded by ROADMAP |

Proposed archive destination, outside the tracked repository:
`C:\Users\Ansible\Documents\EPIP-archive\untracked-docs-2026-08\`, with a
SHA-256 inventory file. The move requires separate owner authorization.

## 8. Data provenance and reproducibility

Every series has a manifest committed under `research/datasets/manifests/`
containing:

- provider name, endpoint pattern, side, timeframe, and instrument code;
- acquisition timestamp, script commit SHA, and tool versions;
- per raw file: path, size, SHA-256, and fetch status;
- per canonical file: SHA-256, row count, first and last timestamp;
- declared gaps, missing months, and session-break policy.

The dataset identity is the SHA-256 of the canonical manifest serialization.
A dataset is reproducible when an independent rebuild from raw files produces
identical canonical checksums.

Candidate providers are evaluated in D00, not selected here. The audit used
Dukascopy public hourly BID candles. Broker MT5 exports (Admirals, XM) are
cross-check candidates with limited history depth.

## 9. Research experiment registry

Every research run appends one record to a versioned JSON Lines registry:

- experiment ID, UTC timestamp, git SHA, and dirty-tree flag;
- hypothesis ID, configuration hash, and pre-registration reference;
- dataset identity and the exact period and partition consumed;
- random seeds;
- metrics with confidence intervals, and controls passed or failed;
- whether any OOS partition was read.

Registry records are append-only. A run absent from the registry has no
standing in any decision.

## 10. Consultation and OOS contamination ledger

| Instrument | Period | Status | Evidence |
| --- | --- | --- | --- |
| EURUSD | 2010-01 to 2018-06 | CONSULTED (selection and OOS) | audit probes T1–T3, 2026-11-22 |
| XAUUSD / GOLD | 2016-01 to 2024-05 | CONSULTED (selection and OOS) | audit probe T4 |
| GOLD (broker) | 2022-06 to 2026-09 | CONSULTED (aggregate and yearly results) | MQL5 V19.12.1 replay files |
| EURUSD, GOLD, BTCUSD, USDCHF | unknown | CONSULTED, periods unknown | V19 master universe; V22 dashboard files |
| USDJPY | unknown | CONSULTED | in `InpMasterSymbols` of V19 since V19.2.2; five V19 versions replay the full universe when `InpReplaySymbols` is empty |
| GBPUSD | unknown | UNVERIFIED — NOT ATTESTED VIRGIN | no EPIP artifact references found; MT5 history caches exist |

Consequences:

- XAUUSD 2024–2026 is **not** a virgin OOS.
- No instrument currently qualifies as virgin OOS.
- The only OOS source that can be guaranteed virgin is a **forward period**
  starting after the Q00 protocol freeze, recorded by the registry.
- GBPUSD may become an OOS candidate only by an explicit owner attestation
  recorded in Q00.

## 11. Causal Elliott research requirements (E00 scope)

E00 prototypes, exclusively under `research/`, must:

1. detect significant swings with a causal amplitude rule (for example an
   ATR-scaled ZigZag), carrying both extreme time and confirmation time;
2. search W1/W2 counts over a sliding window of recent confirmed swings;
3. apply the hard Elliott rules and record invalidations as price evolves;
4. enumerate ranked alternates rather than inferring them from wave count;
5. derive degree from amplitude and nesting, not from timeframe alone;
6. anchor Fibonacci on the selected W1 and derive Fibonacci direction from W1;
7. stamp every emitted fact with its availability time;
8. emit only existing frozen types and pass them, unchanged, to the frozen F01
   rules in-process;
9. never publish a calibrated probability without calibration data.

## 12. Prefix-invariance and non-repainting requirements

For every bar `t` of a series, all outputs available at `t` must be identical
whether computed on the series truncated at `t` or on the full series. This
applies to swings, counts, alternates, anchors, and qualification results.
The requirement is blocking and holds for 100 % of evaluated bars.

## 13. Statistical validation requirements (Q00 scope)

- Hypotheses H1–H7 of the audit are pre-registered before any execution.
- Partitions: development 2010–2018, validation 2019–2021, OOS per section 10.
- Walk-forward on development plus validation: three-year training, one-year
  test, one-year step.
- Costs: real spread when both sides exist, plus declared commission and
  slippage per instrument.
- Mandatory metrics: trade count, expectancy in R with 95 % bootstrap interval,
  t statistic, profit factor, maximum drawdown, results by year and direction,
  comparison with a naive buy-and-hold beta.
- Primary selection criterion: the lower bound of the validation expectancy
  interval, with walk-forward consistency. **Profit factor alone never selects
  a configuration.**

## 14. Multiple-testing and overfitting controls

- Configuration budget: at most 50 per hypothesis and 350 in total, declared
  before execution.
- Correction: Holm adjustment or Deflated Sharpe ratio on validation results.
- Sensitivity: ±20 % parameter perturbation without sign reversal.
- Negative controls: random walk, shuffled directions, and an intentional
  look-ahead control that the harness must flag as unrealistic.
- The audit already showed that selecting among 48 configurations produces an
  in-sample t of about 1.4 on pure noise; Q00 thresholds account for this.

## 15. Research CI specification (D4)

**Contract.** A separate workflow gate runs on every push touching `research/`
and must pass on the exact final SHA of every R01 milestone from D00 onward.

**Required checks.** Black, Ruff, and strict MyPy over `research/`; pytest over
`research/tests/` only; and a guard proving `git diff` on `epip/` is empty for
research milestones.

**Dependencies.** Python 3.13 and repository dev dependencies only. No network
at test time, no external dataset, no MT5. Data-dependent checks run on small
synthetic fixtures committed with the tests.

**Acceptance criteria.** Deterministic results on two consecutive runs; total
runtime under 10 minutes; the canonical production collection and compliance
digest are unchanged by its introduction.

**Implementation milestone.** The workflow file is implemented within D00 only
when the D00 implementation prompt explicitly names
`.github/workflows/research.yml`. Without that explicit authorization, D00
closes with local evidence and Research CI remains pending.

## 16. QA and test strategy

### 16.1 Blocking scenarios

```gherkin
Scenario: Swing causality
  Given a series and its truncation at bar t
  When swings are computed on both
  Then every swing confirmed at or before t is identical

Scenario: W1/W2 confirmation
  Given a W1/W2 count emitted at bar c
  Then its availability timestamp is the close of bar c

Scenario: Non-repainting
  Given a decision emitted at bar t
  When bars after t are appended
  Then the decision at t is unchanged

Scenario: Elliott/Fibonacci anchoring
  Given a qualified W1/W2 count
  Then Fibonacci retracement and extension anchors equal the W1 anchors exactly
  And the frozen rule applicability.fibonacci-wave3 returns SUCCESS

Scenario: No future information
  Given the intentional look-ahead control
  Then the harness flags it as unrealistic

Scenario: Dataset reproducibility
  Given a manifest M
  When the dataset is rebuilt from raw files
  Then every canonical checksum equals M

Scenario: Missing data control
  Given a period absent at the provider
  Then the manifest declares it MISSING and no value is interpolated

Scenario: Timestamp coherence
  Then all bars are UTC, strictly increasing, and unique

Scenario: Identity after re-execution
  Given the same configuration, dataset identity, and seed
  Then the report is byte-identical

Scenario: Partition separation
  Given a selection experiment
  Then no OOS bar is read and any OOS read is refused without a milestone

Scenario: Frozen contract preservation
  Then git diff on epip/ is empty
  And the production collection keeps every predecessor node
  And the compliance inventory and digest are unchanged
```

### 16.2 Test layers

| Layer | Content | Blocking |
| --- | --- | --- |
| Unit | swing rule, count search, Elliott rules, anchoring, manifest builder | yes |
| Integration | prototype output → frozen F01 rules in-process | yes |
| Property | prefix invariance on seeded generated series | yes |
| Regression | full production suite, compliance inventory and digest | yes |
| Performance | prototype over about 100,000 H1 bars in under 60 seconds | indicative |
| Exploratory | setup frequency, expectancy, profit factor, sensitivities | no |

### 16.3 Readiness reproductions

Seven deterministic reproductions were executed against `01c38b55` during the
audit: E-1 positional labelling, E-2 frequency, E-3 anchor contradiction, E-4
F01 rejection of engine outputs, its fixture control, E-5 alternates, and E-6
probability ceiling. All passed as descriptions of current behaviour.

They are **not added by G00**. The proposed file imports private helpers of
frozen test modules, would be neither collected (`testpaths = ["tests"]`) nor
linted by current CI, and would therefore be an ungated artifact. They are
re-authored as self-contained tests under `research/tests/` together with the
Research CI gate (section 15).

## 17. Exact research milestone dependencies

| Milestone | Depends on | Objective | Authorized file scope | Compliance change |
| --- | --- | --- | --- | --- |
| P04-R01-G00 | none | Governance and boundaries | this document; `ROADMAP.md` | none |
| P04-R01-D00 | G00 | Dataset foundation | `research/datasets/**`; `research/tests/**`; `.gitignore` (`data/` only); `docs/project/P04_R01_D00_DATASET_CLOSURE.md`; `ROADMAP.md`; `.github/workflows/research.yml` only if explicitly named | none |
| P04-R01-E00 | G00; D00 for real-data evidence | Causal Elliott research | `research/elliott_causal/**`; `research/tests/**`; `docs/project/P04_R01_E00_CLOSURE.md`; `ROADMAP.md` | none |
| P04-R01-Q00 | D00, E00 | Quantitative validation | `docs/project/P04_R01_Q00_PROTOCOL.md`; `research/harness/**`; `research/experiments/registry.jsonl`; `research/tests/**`; `ROADMAP.md` | none |
| P04-R01-C00 | E00, Q00 | Research closure decision | `docs/project/P04_R01_C00_DECISION.md`; `ROADMAP.md` | none |

E00 development on synthetic series may start once authorized, before D00
closure, but no E00 real-data result has standing before D00 closes. The Q00
protocol is frozen before its first execution.

## 18. G00 closure criteria

G00 is closed when:

- this document and the ROADMAP entry are published in one atomic commit;
- `git diff --check`, Markdownlint, and MkDocs strict pass locally;
- the production collection keeps every predecessor node and the compliance
  inventory and digest are unchanged;
- nothing under `epip/`, no workflow, and no untracked historical document is
  modified;
- HEAD equals `origin/develop`, and Quality, CodeQL, and Documentation pass on
  that exact SHA.

## 19. D00 authorization boundary

D00 is **AUTHORIZED / READY FOR IMPLEMENTATION** within these limits:

- **Objective:** acquire, validate, and manifest the datasets of section 7.
- **Inputs:** decisions D1–D3; candidate provider documentation.
- **Outputs:** acquisition scripts runnable on Windows, canonicalizer,
  manifests, data-quality report, D00 closure record.
- **Tests:** manifest builder, canonicalizer, gap detection, and checksum
  reproducibility on committed synthetic fixtures.
- **Success criteria:** two independent rebuilds produce identical canonical
  checksums; every gap is declared; the provider choice is justified in the
  closure record.
- **Blocking conditions:** provider terms forbid the intended use; network
  unavailable on the acquisition machine; coverage below the declared scope
  without a recorded owner decision.
- **Excluded:** strategy logic, Elliott detection, backtests, performance
  metrics on market data, OOS reads, MT5 changes, and any change under `epip/`.

## 20. Explicit prohibitions

Across all R01 milestones unless a later record states otherwise:

- no change under `epip/` and no frozen contract, identity, or fingerprint
  change;
- no P04-F02, P04-F03, P04-F04, or P05 implementation;
- no MT5 integration and no order of any kind;
- no OOS consumption outside a registered Q00 step;
- no configuration selected on profit factor alone;
- no large dataset committed to Git;
- no deletion, move, rename, or commit of the ten historical documents without
  separate authorization.

## 21. Risks and mitigations

| Risk | Mitigation |
| --- | --- |
| Causal prototype qualifies too few setups for statistics | multi-instrument development data; minimum-frequency gate in E00 |
| Empty-alternates or 300-second expiration conflict | measured, then decided by C00; never bypassed |
| OOS contamination | consultation ledger, registry, forward OOS |
| Provider throttling or terms | slow local acquisition, raw-file cache, alternate provider in D00 |
| Divergence between audit JavaScript probes and Python | Python harness is the reference; probes kept as parity controls |
| Scope drift into `epip/` | blocking diff guard in Research CI |
| Confusing conformance with profitability | three-question separation of section 3 |

## 22. Downstream P04-F02 decision criteria

P04-F02 is **NOT AUTHORIZED / RESEARCH RECONCILIATION REQUIRED** until C00
records one of:

- **A — Continue.** The causal producer emits facts accepted unchanged by the
  frozen F01 rules on real data, at a measured setup frequency sufficient for
  statistics, and Q00 does not show H1 significantly negative in validation.
  A separate producer-integration reconciliation (R01-RQ1) then precedes the
  F02 authorization review.
- **B — Reconcile.** Real-data compatibility or validation requires changing
  strategy rules (for example alternates, anchors, entry zone, expiration).
  A governed reconciliation is opened; frozen records are amended only by that
  reconciliation.
- **C — Suspend.** Wave 3 remains unvalidated; its continuation is suspended in
  favour of other pre-registered hypotheses.

Technical conformance never substitutes for economic validation. No outcome
authorizes demo or live trading.
