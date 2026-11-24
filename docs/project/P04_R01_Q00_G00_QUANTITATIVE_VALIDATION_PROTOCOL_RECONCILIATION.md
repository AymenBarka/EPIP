# P04-R01-Q00-G00 — Quantitative Validation Protocol and Research Readiness Reconciliation

Status: **CLOSED / FROZEN**

Approved by the owner on 2026-11-24 (revision 2, with final corrections QG-15
to QG-20). Q00 sub-milestones become eligible for individual authorization.
This record authorizes no implementation, download, backtest, optimization,
OOS read, workflow change, MT5 operation, or order.

## 1. Authority

This record governs P04-R01-Q00 under
[P04-R01-G00](P04_R01_G00_RESEARCH_GOVERNANCE_AND_CAUSAL_ELLIOTT_READINESS.md)
sections 9, 10, 13, 14, 17, and 22, as amended by
[P04-R01-G00-A01](P04_R01_G00_A01_TICK_DATA_SCOPE_AMENDMENT.md), and builds on
[P04-R01-D00](P04_R01_D00_DATASET_CLOSURE.md) and
[P04-R01-E00](P04_R01_E00_CLOSURE.md). Frozen semantics come from
[P04-R00](P04_R00_ELLIOTT_FIBONACCI_SETUP_RECONCILIATION.md),
[P04-F00-R02](P04_F00_R02_NORMATIVE_CONFIGURATION_RECONCILIATION.md),
[P04-F01-R01](P04_F01_R01_ELLIOTT_FIBONACCI_WAVE3_SETUP_QUALIFICATION_CONTRACT.md),
and [P04-F02-R01](P04_F02_R01_GEOMETRY_A07_RR_OWNERSHIP_RECONCILIATION.md).
None of them is reopened or changed.

## 2. Baseline

Measured at `2044663147eafde32f1b3825a85faf465997fbfa` (`develop`, HEAD equal
to `origin/develop`, tracked tree clean, 18 historical untracked artifacts
preserved):

| Item | Value |
| --- | --- |
| Production pytest collection | 3127 |
| Compliance inventory / digest | 612 / `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |
| Research tests | 251 (D00 164, E00 87) |
| Consultation ledger | 2 records, both TECHNICAL (E00, 2026-11-24) |
| Local datasets | D00 technical sample only (2012-03-12 to 2012-03-17) |

## 3. Reconciliations recorded by this milestone

| ID | Finding | Resolution |
| --- | --- | --- |
| QG-1 | G00 section 13 cites "hypotheses H1–H7 of the audit", which exist only in an untracked owner document. | Section 7.1 records their titles. Q00 pre-registers H1 only; each of H2–H7 needs its own pre-registration milestone. |
| QG-2 | G00 section 8 requires committed manifests under `research/datasets/manifests/`; D00 keeps manifests in the local registry. | From D01 onward every dataset manifest is committed there (hashes and coverage only). |
| QG-3 | G00 section 17 gives Q00 no write access to `research/datasets/**` or the workflow. | Data work is D-family (D01, D02) with the D00 file scope; the workflow change is Q00-CI00 (section 16). |
| QG-4 | G00 section 17 names `P04_R01_Q00_PROTOCOL.md`. | This record is the normative protocol; that file becomes the pre-registration record of Q00-I00, frozen before the first real-data run. |
| QG-5 | Calendar `ny-1700-close/1` has no holidays; the E00 loader refuses unexplained hours. | D01 introduces a versioned calendar with a sourced holiday table; residual gaps follow section 6.6. |
| QG-6 | Research CI excludes `research/elliott_causal` from static checks and coverage. | Still **open**; closed only by Q00-CI00 (section 16). |
| QG-7 | Revision 1 quarantined 2022 onward without an end, and dated FINAL_OOS from the Q00 pre-registration. | Section 5: historical boundaries, permanent quarantine, unverified intermediate period, prospective FINAL_OOS only after the **final** freeze, each with its own authorization. |
| QG-8 | Full tick acquisition is estimated at 600–1,000 hours. | Section 6 compares architectures A, B, and C. A remains the governed baseline; B is rejected; C is a candidate accelerator subject to a probe, an equivalence test, and an A01 amendment. |
| QG-9 | Excluding positions open at partition end biases results. | Section 11.4: censored trades are included at mark-to-market, with a pre-registered sensitivity analysis, a 5 % censoring ceiling, and boundary rules. |
| QG-10 | Walk-forward and validation isolation were conflated. | Section 11: Protocol A (fixed-parameter validation) is **primary**; Protocol B (adaptive walk-forward) is secondary. |
| QG-11 | 4 variants × 30 configurations exceeds 50 per hypothesis. | Section 12: the four variants belong to H1, so the ceiling is collective. A compliant reduced design uses exactly 50 configurations; no amendment is needed. |
| QG-12 | Confidence (0.60 × probability + 0.40 × confluence ≥ 0.70) and structure alignment cannot be evaluated honestly. | Section 7.3: the qualification status ladder. H1-G is a **partial-profile** governed variant, `FULL_PROFILE_NOT_EVALUATED`. |
| QG-13 | Execution edge cases were incomplete. | Section 10.4: a single precedence order and one outcome per event. |
| QG-14 | Statistical reproducibility was incomplete. | Section 13: Holm, adjusted bounds, Deflated Sharpe inputs, Romano–Wolf, week-block bootstrap, paired comparisons, controls, seeds, and minimums. |
| QG-15 | Planned RR and realized R used inconsistent entries and risk distances. | Section 10.5: planned and executed entry and risk are distinct; A07 RR uses planned values; one primary research R uses the executed risk; signs and costs are counted once. |
| QG-16 | Parameter sensitivity is executed only for H1-G and H1-M, yet was required of every variant. | Section 13.10: H1-P and H1-PM carry `SENSITIVITY_NOT_EVALUATED` and can never reach `DEMONSTRATED FOR SELECTION`. |
| QG-17 | Sensitivity scope, rounding, and deduplication were unspecified. | Section 12.4: sensitivity and cost/latency scenarios apply only to the Protocol A selections of H1-G and H1-M; deterministic rounding; identity deduplication; Protocol B adds nothing. |
| QG-18 | Bootstrap edge cases were unspecified. | Section 13.11: invalid replicates, degenerate samples, undefined statistics, and inconclusive variants, all kept in a fixed four-member Holm family with p = 1. |
| QG-19 | C1 equivalence mixed data and behaviour. | Section 6.4: Level 1 (data) and Level 2 (behaviour, which needs Q00-I00); dependencies reconciled in section 17. |
| QG-20 | Financing and overnight costs were not addressed. | Section 10.6: financing is excluded and not fabricated; results carry `FINANCING_EXCLUDED`; rollover exposure is reported; commission units are defined. |

On G00 section 13: its "primary selection criterion" (the lower bound of the
expectancy interval) is applied on **development** to select configurations in
Protocol A. On validation it serves only as the **acceptance** criterion, as
the owner directed under QG-10. G00 is not amended.

## 4. E00 evidence certification

| Item | Status |
| --- | --- |
| Causal swing confirmation (strictly after the extreme) | certified |
| Prefix invariance | 100 % on executed synthetic and real coverage |
| Rolling W1/W2 search (last 12 pivots) | certified |
| Shared Elliott/Fibonacci anchors | 0 continuity failures |
| Frozen F01 compatibility | single counts accepted unchanged |
| Alternate-count restriction (E00-F2) | documented, not bypassed |
| Frozen probability and confidence | `0.0` meaning "not estimated"; uncalibrated |
| Dataset identities | `a4c33c19042a…` EURUSD H1, `ce4d98346a84…` XAUUSD H1 |
| Consultation | TECHNICAL only, ledger before read; no OOS read |

The technical week has no statistical standing and supports no profitability
inference.

## 5. Partitions, contamination, and OOS

### 5.1 Two dimensions

**Partition** is how data may be used: TECHNICAL, DEVELOPMENT, VALIDATION,
QUARANTINED, UNVERIFIED_INTERMEDIATE, or FINAL_OOS. **Contamination status**
is what has already been seen: CONSULTED, UNVERIFIED, or ATTESTED_VIRGIN.

### 5.2 Historical periods

The **historical boundary** `H_END` is 2026-12-01 00:00 UTC, the first month
start after this record's approval. Every timestamp before `H_END` is
historical.

| Instrument | Period (UTC, end excluded) | Partition | Contamination | Evidence |
| --- | --- | --- | --- | --- |
| EURUSD, XAUUSD | 2012-03-12 to 2012-03-17 | TECHNICAL, inside development | CONSULTED, structure only | D00, E00 ledger |
| EURUSD | 2010-01-01 to 2019-01-01 | DEVELOPMENT | CONSULTED; results seen for 2010-01 to 2018-06 | probes T1–T3 |
| XAUUSD | 2010-01-01 to 2019-01-01 | DEVELOPMENT | CONSULTED; results seen from 2016-01 | probe T4 |
| EURUSD | 2019-01-01 to 2022-01-01 | VALIDATION | CONSULTED, universe-level, periods unknown | V19, V22 |
| XAUUSD | 2019-01-01 to 2022-01-01 | VALIDATION, reduced standing | CONSULTED, results seen | probe T4 |
| XAUUSD | 2022-01-01 to 2026-10-01 | **QUARANTINED, permanent** | CONSULTED, results seen | T4 to 2024-05; V19 replay 2022-06 to 2026-09 |
| EURUSD | 2022-01-01 to `H_END` | UNVERIFIED_INTERMEDIATE | CONSULTED, universe-level | V19, V22 |
| XAUUSD | 2026-10-01 to `H_END` | UNVERIFIED_INTERMEDIATE | UNVERIFIED | no record, not presumed virgin |
| EURUSD, XAUUSD | before 2010-01-01 | not in Q00 | UNVERIFIED | — |
| GBPUSD, USDJPY | any | not in Q00 | GBPUSD UNVERIFIED; USDJPY CONSULTED | G00 section 10 |

### 5.3 Prospective periods and FINAL_OOS

- **`F_STAR`** is the commit that freezes the final model, configuration,
  selection rules, and strategy decision. It can exist only after C00 decides
  A (continue), together with any reconciliation C00 requires.
- Data from `H_END` up to the first month start after `F_STAR` is
  **UNVERIFIED_INTERMEDIATE**. It is never FINAL_OOS, even if never read. It
  may become extra development data only through an amendment.
- **Earliest FINAL_OOS eligibility** is the first UTC month start strictly
  after `F_STAR`. Its minimum length and trade count are pre-registered at
  `F_STAR`.
- FINAL_OOS **collection** and **evaluation** are two separate future
  milestones, both requiring explicit authorization after C00. Neither is
  authorized here.

### 5.4 Rules

1. No period is ATTESTED_VIRGIN, and no period is inferred virgin because Q00
   has not read it.
2. QUARANTINED and UNVERIFIED_INTERMEDIATE reads are refused in code. FINAL_OOS
   reads are refused in code until their milestone exists.
3. XAUUSD validation is always reported separately, and pooled results are
   reported with and without XAUUSD.
4. Each read appends a ledger record with its partition **before** content
   access.
5. Validation data is neither acquired nor read until the Protocol A selection
   record exists (section 11.2).
6. **Q00 yields selection evidence on consulted data, never confirmation.**

## 6. Acquisition architecture

### 6.1 Compared architectures

Scope: EURUSD and XAUUSD, 2010–2021. The basis is D00: 19.2 KB per
instrument-hour (2012) and 150–250 files per hour of effective throughput
under throttling.

| Criterion | A. Complete ticks (`.bi5`) | B. Provider H1 plus targeted ticks | C. Alternative bulk mechanisms |
| --- | --- | --- | --- |
| Requests | ≈ 150,800 hour files + 576 candle files | 576 candle files + per-signal windows (unbounded without a holding cap) | C1 Dukascopy JForex Historical Data Manager or web export: unknown, few large jobs; C2 MT5 broker ticks: terminal sync |
| Storage | 2.3–6 GB raw; 4–11 GB canonical | < 1 GB | C1 comparable to A, uncompressed CSV larger; C2 broker-dependent |
| Wall clock | 600–1,000 h at observed throughput (≥ 42 h theoretical at 1 req/s) | short for candles; windows iterative | C1 unmeasured; C2 fast but shallow |
| Availability | full 2010–2021 per D00 behaviour | full for candles | C1 same provider history; C2 typically a few years only |
| Access limits | throttling (HTTP 503), undocumented endpoint | same endpoint | C1 needs a demo login (owner-entered) and a desktop app; C2 broker-specific |
| Causality | analytics on tick-derived H1 (A01 authoritative) | analytics on **provider** H1, which differs from tick-derived H1 for XAUUSD (D00: 94 of 232 bars) | C1 identical if ticks equal; C2 different provider identity |
| Execution accuracy | full tick sequencing | complete only if every window and lifetime is covered | C1 as A if equivalent; C2 gaps filled by generated ticks are not acceptable |
| Missing-data risk | explicit hour statuses | high: window selection errors are silent | C1 export failures must be detected per hour; C2 silent tick generation |
| G00 and A01 | compliant | conflicts with A01 (H1 never stands in for ticks; tick-derived analytics) | C1 changes the raw format (CSV instead of `.bi5`): A01 amendment; C2 is a comparison source only (owner decision) |
| Required amendments | none | A01 and Q00-G00 | C1: A01 raw-format amendment plus equivalence proof |

### 6.2 Decision

- **A is the governed baseline.**
- **B is rejected.** It cannot reproduce the governed semantics:
  - its structural signals come from provider H1, which is not equivalent to
    tick-derived H1 for XAUUSD;
  - complete position lifetimes are unbounded, because there is no maximum
    holding time, so tick coverage would have to be extended trade by trade
    according to realized price paths, which is outcome-dependent acquisition;
  - the 100 time-shuffled negative-control sets and each grid configuration
    multiply the windows.
- **C2 (MT5)** remains a comparison source only.
- **C1 (Dukascopy JForex or web export)** is a candidate accelerator. It may
  replace A's transport only after:
  1. an owner-run probe milestone (D01-P) exports the D00 technical week and
     one D01-B1 month;
  2. Level 1 equivalence (section 6.4) passes in D01-P;
  3. Level 2 equivalence passes after Q00-I00 exists;
  4. an A01 amendment admits the CSV raw format with dual SHA-256 and
     provenance.

  Neither C1 acquisition nor an A01 change is authorized by this record.

If neither A nor C1 is operationally acceptable, any reduction of the
2010–2021 span requires an explicit amendment of this record. Coverage is
never reduced silently.

### 6.3 Batching under A

The full history is acquired **incrementally in separately authorized
batches**:

1. **D01-B1**: EURUSD and XAUUSD, 2018-01-01 to 2018-07-01, DEVELOPMENT. It
   measures density, throughput, and quality: ≈ 6,240 requests, 95–250 MB raw,
   25–42 h.
2. **D01-B2 and later**: the remaining development months, at most 12
   instrument-months per batch.
3. **D02**: validation 2019–2021, only after the Protocol A selection record.

No batch authorizes the next.

### 6.4 Equivalence test (for C1, and any future alternative)

**Level 1 — data equivalence** (certifiable in D01-P, once D01-B1 exists).
For every compared instrument-hour, the alternative and the `.bi5` path must
agree on:

- exact tick counts;
- millisecond timestamps in the same order;
- BID and ASK in integer points;
- quoted volumes normalized to integer millionths;
- canonical SHA-256 values;
- derived H1/H4 `dataset_id` values;
- E00 causal events.

**Level 2 — behavioural equivalence** (certifiable only after Q00-I00 exists).
On fixed, pre-registered configurations, the two paths must produce:

- identical Q00 execution outcomes;
- identical outcome attribution;
- identical deterministic reports.

A single difference at either level rejects the alternative for that
instrument. Behavioural equivalence is never claimed before its Level 2
evidence exists, and no C1-acquired data may enter Q00-V00 before both levels
pass.

### 6.5 Acquisition limits (A)

Each window covers one instrument-month:

- planned requests at most 600 and per-run requests at most 1,500, with
  retries counted;
- per-run download ceiling 100 MB;
- at least one second between requests and at most 5,000 requests per UTC
  day;
- 30-second default timeout (up to 120 seconds); 4 retries with 2–60 s
  backoff;
- abort after 5 consecutive failures; resume with verification on relaunch.

Scheduled weekend-closure hours are not requested; they are declared from the
calendar. Provider terms are re-confirmed by the owner before each batch.

### 6.6 Manifests and quality gates

- One tick dataset per instrument-month, with derived H1/H4 and provider H1
  candles. Manifests are committed under `research/datasets/manifests/`.
- A month is usable only if every planned hour is POPULATED or EXPECTED_CLOSURE
  under the versioned calendar.
  - A residual gap is retried in three separate runs, then recorded with an
    owner decision: exclude the month, or declare the hour MISSING.
- Duplicate-tick rejection stops acquisition pending a policy amendment.
- H1 cross-check:
  - an EURUSD deviation blocks the month pending investigation;
  - XAUUSD deviations are reported only.
- Each batch is rebuilt in a fresh data root and must reproduce every
  `dataset_id`.

## 7. Hypotheses, variants, and qualification standing

### 7.1 Hypotheses

| ID | Title | Q00 status |
| --- | --- | --- |
| H1 | Elliott W3 + Fibonacci, frozen P04 profile | **pre-registered here** |
| H2 | Elliott + market structure (BOS in the W3 direction) | own pre-registration required |
| H3 | Elliott + liquidity (sweep below W2) | own pre-registration required |
| H4 | Elliott + H4 trend regime | own pre-registration required |
| H5 | ENITREND alone | own pre-registration and M15 data required |
| H6 | V19 H4 regime alone | own pre-registration required |
| H7 | V19 hybrid (H4 + H1 Elliott + M15 ENITREND + VWAP) | own pre-registration and M15 data required |

### 7.2 H1 variants

All variants use the frozen geometry: entry zone 0.618–0.705 of W1, stop at W1
origin, target at the 1.618 extension, minimum RR 3.0.

| Variant | Count mode | Entry | Standing |
| --- | --- | --- | --- |
| H1-G | FAITHFUL | limit at the A07 zone bound, valid 300 s after evaluation | governed, **partial profile** |
| H1-P | PRIMARY_ONLY | same as H1-G | research counterfactual |
| H1-M | FAITHFUL | market at the first executable tick | research counterfactual |
| H1-PM | PRIMARY_ONLY | market | research counterfactual |

### 7.3 Qualification status ladder

Each published primary carries every applicable status. Statuses are
research labels mapped onto existing contracts; they create no production
type.

| Status | Meaning | Contract |
| --- | --- | --- |
| `STRUCTURAL_CAUSAL` | E00 causal primary count | E00 |
| `F01_GOVERNED` / `F01_REJECTED` | frozen F01 chain class C / D | P04-F01 |
| `RR_GOVERNED` / `RR_REJECTED` | frozen A07 E07 accepts or rejects RR ≥ 3.0 at the planned entry | A07 E07 |
| `RR_NON_GOVERNED` | fallback if A07 E07 cannot be invoked without F02 facts | — |
| `STRUCTURE_ALIGNMENT_NOT_EVALUATED` | the mandatory market-structure alignment (P04-R00) is not evaluated; its producer has no causal audit | P04-R00 |
| `CONFIDENCE_UNCALIBRATED` | the frozen confidence gate (0.60 × Elliott probability + 0.40 × Fibonacci confluence ≥ 0.70, A07 E08) is not evaluable: no calibrated input exists, and none is fabricated | P04-R00, A07 E08 |
| `FULL_PROFILE_NOT_EVALUATED` | always set in Q00: complete P04 signal eligibility is not established | P04-R00 |
| `RESEARCH_COUNTERFACTUAL` | H1-P, H1-M, H1-PM | this record |

Consequences:

- H1-G describes F01- and RR-qualified setups, a **superset** of complete
  frozen-profile signals. It never stands for the complete profile.
- The uncalibrated E00 ranking score is never converted into a probability.
- Any probability calibration or structure-alignment evaluation is a separate
  future milestone. Calibration would be trained on authorized development data
  only and frozen before any validation read.
- F02, F03, and F04 are not implemented.

## 8. Three research questions

| Question | Diagnostics | Outcome labels |
| --- | --- | --- |
| A. Structure | pivots, latency, candidates, F01 acceptance by mode with Wilson 95 % intervals, alternate cardinality, rejection reasons, by symbol, year, direction, and causal ATR regime tercile | `PASS` if prefix invariance and anchor continuity hold and at least 30 `F01_GOVERNED` setups per instrument exist in development; otherwise `INSUFFICIENT FREQUENCY` |
| B. Executability | outcome attribution (section 9.3), fill rates with Wilson intervals, distances to zone, stop, and target at evaluation, first-touch delay | `EXECUTABLE` if H1-G reaches at least 100 fills across development and validation; otherwise `NOT EXECUTABLE UNDER FROZEN TIMING`, and H1-M is reported as a counterfactual |
| C. Expectancy | sections 11–13 | `DEMONSTRATED FOR SELECTION`, `NOT DEMONSTRATED`, or `INCONCLUSIVE` |

The three answers are always reported separately.

## 9. Alternates and temporal semantics

### 9.1 Alternates (E00-F2)

Both modes are measured for every run:

- candidate frequency;
- F01 acceptance rate;
- alternate cardinality;
- distribution by symbol, direction, year, and regime;
- rejection reasons;
- paired outcome consequences (section 13.6).

F01 is not modified. Alternates are never removed to improve results. The
decision belongs to C00.

### 9.2 Timeline

| Instant | Definition |
| --- | --- |
| `t_extreme` | start of the bar holding the pivot extreme |
| `t_confirm` | close of the bar confirming the pivot; W2 completion is known from here only |
| `t_eval` | `t_confirm` |
| `t_publish` | `t_eval`; evidence age is 0 s, compatible with `max_age_seconds = 0` |
| `t_submit` | `t_publish + L`, with L = 1 s (sensitivity: 5 s) |
| `t_expire` | `t_eval + 300 s` (frozen `expiration_seconds`) |
| earliest executable tick | the first tick with timestamp ≥ `t_submit` |

The confirmation latency is not assumed to invalidate the 300 s signal; it is
measured. A proven incompatibility is deferred to C00. Expiration and
freshness are unchanged in Q00.

### 9.3 Outcome attribution

Every published primary receives exactly one class. Classes are checked in
this order:

1. `F01_REJECTED`;
2. `SKIPPED_OVERLAP`;
3. `RR_BELOW_MINIMUM`;
4. `INVALIDATED_BEFORE_SUBMISSION`;
5. `INVALIDATED_BEFORE_FILL`;
6. `EXPIRED_NO_FILL`;
7. `EXPIRED_AT_BOUNDARY`;
8. `DATA_INCOMPLETE`;
9. `FILLED`, which then ends as `STOPPED`, `TARGET`, or `CENSORED`.

For `EXPIRED_NO_FILL`, the first zone touch up to 24 H1 bars later is recorded
descriptively. No trade or P&L is computed for any validity other than 300 s.

## 10. Execution model

### 10.1 Prices and direction

UP is a BUY and DOWN a SELL. A BUY enters on ASK and its stop and target
trigger on BID; a SELL is the mirror image. Fills never use a historical pivot
extreme.

### 10.2 Orders and costs

- **Frozen limit.** Placed at `t_submit` at the A07 zone bound: the upper bound
  for a BUY, the lower bound for a SELL. It fills at the limit price, with no
  price improvement and no slippage.
- **Market counterfactual.** Fills at the first executable tick's price plus
  adverse slippage.
- **Stops.** Fill at the triggering tick's price, gaps included, plus adverse
  slippage.
- **Targets.** Fill at the target price, with no improvement.

| Instrument | Commission per side (price units: USD per EUR; USD per ounce) | Adverse slippage (market and stop), price units | Sensitivity |
| --- | --- | --- | --- |
| EURUSD | 0.000035 (equivalent to USD 3.50 per 100,000 EUR) | 0.00002 | commission and slippage × 1.5 and × 2 |
| XAUUSD | 0.035 (equivalent to USD 3.50 per 100 oz) | 0.05 | commission and slippage × 1.5 and × 2 |

Slippage always moves against the trade: up for a BUY fill, down for a SELL
fill.

### 10.3 Lifecycle

- At most one pending-or-open order per instrument. A later signal is
  `SKIPPED_OVERLAP`; the earlier order keeps priority.
- Positions are held through closures. There is no maximum holding time.

### 10.4 Precedence (one deterministic outcome per event)

Ticks are processed by timestamp, then in D00 source order. All ticks sharing
one timestamp form a **simultaneous group**: within a group, invalidation and
stop take precedence over fills and targets.

| Case | Outcome |
| --- | --- |
| Stop level crossed between `t_eval` and `t_submit` | `INVALIDATED_BEFORE_SUBMISSION`; no order |
| Stop level crossed while the order is pending, before a fill | order cancelled; `INVALIDATED_BEFORE_FILL` |
| Entry and stop conditions in the same tick or group | `INVALIDATED_BEFORE_FILL`; no fill through an invalidated setup |
| Gap through both the entry limit and the stop | `INVALIDATED_BEFORE_FILL` |
| Second signal while an order is pending or open | `SKIPPED_OVERLAP` |
| Tick at exactly `t_expire` | eligible (inclusive); later ticks are not |
| Stop and target in the same tick or group | `STOPPED` |
| Exit checks after a fill | start at the next distinct timestamp |
| RR decision and research R | defined in section 10.5 |
| Pending or open lifetime touching an hour not POPULATED or EXPECTED_CLOSURE | `DATA_INCOMPLETE`; scheduled closures are not missing data |

### 10.5 Planned RR versus realized R (QG-15)

Let s = +1 for a BUY and s = −1 for a SELL. S is the stop (W1 origin) and T the
target (1.618 extension).

| Quantity | Definition |
| --- | --- |
| Planned entry `E_p` | limit: the A07 zone bound; market: the last entry-side quote (ASK for a BUY, BID for a SELL) at or before `t_submit` |
| Executed entry `E_x` | limit: the limit price; market: the first executable entry-side tick price, moved by s × slippage |
| Planned risk `D_p` | `abs(E_p − S)` |
| Executed risk `D_x` | `abs(E_x − S)` |
| Executed exit `X_x` | stop: the triggering exit-side tick price, gaps included, moved by −s × slippage; target: T; censored: the last exit-side quote before the boundary, moved by −s × slippage |
| Commissions `K` | entry commission + exit commission, in price units |

- **Frozen A07 E07 RR acceptance** uses `E_p`, S, and T only. It is evaluated
  by frozen A07 (`RR_GOVERNED`) or, in the fallback, by a labelled
  research mirror (`RR_NON_GOVERNED`). Research code never overrides it.
- **Primary research R** (the only primary formula):
  `R = (s × (X_x − E_x) − K) / D_x`.
- **Planned-risk R** (reported separately): `R_p = (s × (X_x − E_x) − K) / D_p`.
  For limit fills, `E_x = E_p`, so `R_p = R`.
- **No double counting.** Spread is embedded in the side-specific prices.
  Slippage and gaps are embedded once, in `E_x` and `X_x`. `K` contains
  commissions only. A censored trade is valued once, at its executed exit as
  defined above.
- **Fail-closed.** If `D_x ≤ 0` (an executed entry at or beyond the stop),
  the event is `INVALIDATED_BEFORE_FILL` (section 10.4), never a trade.
- **Stop-valued censoring sensitivity** (section 11.4) sets
  `X_x = S` moved by −s × slippage.
- R is dimensionless. No account-currency P&L, position sizing, or leverage is
  modelled.

### 10.6 Financing and holding costs (QG-20)

Overnight financing, swaps, and weekend or triple rollovers are **not
modelled**:

- no governed historical financing series is authorized or acquired;
- no rate is fabricated or assumed.

Consequences:

- Every economic result carries `FINANCING_EXCLUDED`. It is described as "net
  of spread, commission, and slippage, excluding financing", never as fully
  realistic net profitability.
- Per trade, the harness reports the holding time, the number of 17:00 New York
  rollovers crossed, and the number of weekends crossed. Their distributions
  are reported per variant, so that C00 can judge the financing exposure.
- Any financing model needs a future amendment and dataset authorization, and
  stays within the approved budget or amends it.

## 11. Validation protocols and boundaries

### 11.1 Two protocols

| | Protocol A — fixed-parameter validation (**primary**) | Protocol B — adaptive walk-forward (**secondary**) |
| --- | --- | --- |
| Selection data | development 2010-03-01 to 2019-01-01 | for each test year Y, training years Y−3 to Y−1 |
| Evaluation | validation 2019-01-01 to 2022-01-01, configuration unchanged | test years 2013 to 2021 |
| Validation years used for training | never | **yes**: 2019 and 2020 are training inputs for the 2020 and 2021 folds |
| Order | runs first; its selection is frozen before any validation acquisition or read | runs only after Protocol A's validation result is recorded |
| Standing | selection evidence on consulted data | adaptive research evidence; never called fixed validation |

Neither protocol is final confirmatory OOS.

### 11.2 Selection rule (deterministic)

Selection runs per variant. A configuration is eligible with at least 100
pooled and 30 per-instrument trades in the selection data. The selected one
maximizes the one-sided 95 % lower bound of mean net R (section 13). Ties
break by, in order:

1. higher mean net R;
2. smaller `threshold_atr`;
3. smaller `atr_period`;
4. smaller `window_pivots`;
5. lexicographic configuration hash.

The Protocol A selection is appended to the experiment registry and committed
before D02 is authorized.

### 11.3 Folds, warm-up, purging, embargo

- **One run per configuration.** Every configuration runs as one continuous
  causal simulation from 2010-01-01, with the first two months as engine
  warm-up and no signals counted.
- **Protocol A.** The validation run starts its engine on development H1 bars
  from 2018-07-01 as warm-up and counts only signals with `t_eval` on or after
  2019-01-01.
- **Protocol B.** A fold's test trades are the selected configuration's trades
  with `t_eval` in year Y.
- **Purging.** Selection metrics include only trades whose entire lifetime
  ends inside the training window. Trades open at the training end are
  excluded from selection, so no test-period outcome can influence selection.
- **Embargo.** None beyond purging is required, because the engine is causal
  and the test signals follow the training end.

### 11.4 Censoring and partition boundaries

- **No crossing.** Orders and positions never read ticks beyond their
  partition's end:
  - development ends at 2019-01-01;
  - validation ends at 2022-01-01;
  - Protocol B fold boundaries inside one partition do not stop positions.
- **Pending at a boundary.** An order still pending at the boundary is
  `EXPIRED_AT_BOUNDARY`.
- **Censored positions.** A position open at the boundary is `CENSORED`. Its
  primary valuation is mark-to-market at the last executable exit-side quote
  before the boundary (BID for a BUY, ASK for a SELL), with adverse slippage in
  the executed exit and exit commission in `K`, each counted once
  (section 10.5).
- **Reporting.** Realized and unrealized outcomes are always reported
  separately. The primary outcome includes censored trades at mark-to-market.
  Pre-registered sensitivities: realized-only, and censored valued at the stop
  (section 10.5). No adverse open position is discarded.
- **Ceiling.** If censored trades exceed **5 %** of filled trades in an
  evaluation set, that set is `INCONCLUSIVE`.
- **No cross-partition reads.** A development trade is never resolved with
  validation ticks.

### 11.5 Conditions producing INCONCLUSIVE

An evaluation set is `INCONCLUSIVE` if:

- the trade minimums are not met (section 13.8);
- censoring exceeds 5 % of filled trades;
- `DATA_INCOMPLETE` exceeds 2 % of published primaries;
- the bootstrap has fewer than 26 weeks containing trades.

## 12. Configuration budget

### 12.1 Meaning

G00 section 14 sets 50 configurations per **hypothesis** and 350 in total. H1
variants belong to H1, so the 50 ceiling applies to all four collectively.

A **configuration** is a distinct tuple (variant, engine parameters, execution
scenario) whose outcome statistics are computed on development or validation
data.

### 12.2 Counting

| Item | Counts toward the budget | Reason |
| --- | --- | --- |
| Parameter grid points per variant | yes | candidate strategies |
| Strategy variants | yes, through their grid points | distinct strategies |
| ±20 % sensitivity configurations | yes | evaluated parameter sets |
| Cost and latency scenarios | yes, conservatively | evaluated execution scenarios |
| Negative controls | no; capped and pre-registered (section 13.7) | null models, never selectable |
| Bootstrap resamples | no | inference on one configuration |
| Walk-forward folds (Protocol B) | no | reuse the same grid; no new configuration |
| Deterministic reruns | no | identical computation |

### 12.3 Compliant design (exactly 50 of 50 for H1; 50 of 350 overall)

- Grid: `threshold_atr` ∈ {2.5, 3.0, 3.5} × `atr_period` ∈ {10, 14, 20}, giving
  9 configurations.
- Fixed: `window_pivots` 12, `max_alternates` 4, `max_degree_gap` 1. The
  frozen geometry, RR, expiration, and freshness are never varied.

| Item | Configurations |
| --- | --- |
| H1-G, H1-P, H1-M, H1-PM × 9 | 36 |
| ±20 % on `atr_period` and `threshold_atr` for the H1-G and H1-M selections | 8 |
| Cost × 1.5, cost × 2, latency 5 s for the H1-G and H1-M selections | 6 |
| **Total** | **50** |

There is no reserve. Any further configuration requires an amendment. The
30-point grid of revision 1 (148 configurations) is withdrawn; it would need an
explicit owner amendment counting each variant as a hypothesis.

### 12.4 Sensitivity scope, rounding, and deduplication (QG-17)

- **Scope.** The 8 parameter-sensitivity configurations and the 6 cost and
  latency configurations apply **only** to the Protocol A selections of H1-G
  and H1-M. They are evaluated on the Protocol A validation set and are never
  eligible for selection.
- **One parameter at a time.** Sensitivities change one parameter from the
  selection: `atr_period` down, `atr_period` up, `threshold_atr` down,
  `threshold_atr` up.
- **Rounding.**
  - `atr_period`: `floor(0.8 × p + 0.5)` and `floor(1.2 × p + 0.5)`, in
    integer arithmetic. This gives 10 → 8 and 12; 14 → 11 and 17; 20 → 16
    and 24.
  - `threshold_atr`: 0.8 × t and 1.2 × t in exact decimal arithmetic, rounded
    half-up to two decimals. This gives 2.5 → 2.00 and 3.00; 3.0 → 2.40 and
    3.60; 3.5 → 2.80 and 4.20.
- **Deduplication.** A configuration's identity is the SHA-256 of the canonical
  JSON of (variant, engine parameters, execution scenario). A perturbation that
  equals an existing identity (for example, threshold 2.5 perturbed up to 3.00,
  a grid point) reuses that result and is not counted again.
- **Ceiling.** The budget counter counts unique identities and refuses any
  identity beyond 50 unique H1 configurations.
- **Protocol B** reuses only the nine-point grids. It generates no sensitivity,
  cost, or latency configuration, no adaptive search, and no variant.

## 13. Statistical protocol

### 13.1 Primary outcome

Mean primary research R (section 10.5) per filled trade, with censored trades
valued as in sections 10.5 and 11.4. It is a statistic only, never an A07 RR
decision, and it carries `FINANCING_EXCLUDED` (section 10.6).

### 13.2 Bootstrap

- Stationary block bootstrap (Politis–Romano) over **UTC calendar weeks**,
  Monday start, by trade entry time.
- Weeks without trades are retained.
- Instruments are resampled **jointly** by week, preserving cross-instrument
  dependence.
- Mean block length 4 weeks; B = 10,000.
- Statistic: total R divided by the trade count of each resample.

### 13.3 Hypothesis test and Holm

- **Hypotheses.** For variant v, H0: mean net R ≤ 0.
- **p-value.** p_v = (1 + #{b : mean*_b − mean ≥ mean}) / (B + 1), on the
  centered bootstrap distribution.
- **Family.** The four H1 variants on Protocol A validation, α = 0.05.
- **Holm.** Sort the p-values ascending. Reject p_(i) while
  p_(i) ≤ α / (m − i + 1), stopping at the first failure.

### 13.4 Multiplicity-adjusted bounds

The one-sided lower bound at level α / m = 0.0125 (Bonferroni, which is
conservative and consistent with Holm) is the 1.25th percentile of the
bootstrap means. Acceptance needs both a Holm rejection and an adjusted lower
bound greater than 0.

### 13.5 Deflated Sharpe and Romano–Wolf

- **Deflated Sharpe ratio** (Bailey and López de Prado), reported, not
  decisive. Inputs: the per-trade Sharpe ratio of the selected configuration;
  trade count T; skewness and kurtosis of trade R; trials N = 50; and the
  variance of per-trade Sharpe across the 36 development grid results.
- **Romano–Wolf** stepdown on the 36 development grid results, using
  studentized means with the same week-block bootstrap. Reported as
  exploratory.

### 13.6 Paired FAITHFUL versus PRIMARY_ONLY

For each configuration, H1-G is compared with H1-P (and H1-M with H1-PM):

- the difference in mean R and in trade count, using identical resampled
  weeks for both;
- a separate mean R for trades present only in PRIMARY_ONLY, which isolates
  the effect of the alternates restriction.

### 13.7 Negative controls (pre-registered, not counted as configurations)

| Control | Requirement |
| --- | --- |
| Random walk: 20 seeded synthetic series matching development length and volatility | adjusted lower bound ≤ 0 in at least 19 of 20; otherwise the harness is void |
| Direction inversion of the selected configurations on the same data | inverted adjusted lower bound > 0 makes the result `NOT DEMONSTRATED` |
| 100 seeded time-shuffled signal sets (same hours-of-week distribution) | the real mean must exceed the 95th percentile of shuffled means for acceptance |
| Look-ahead control (entry at the pivot extreme) | must be flagged by the causality checks; otherwise the harness is void |

### 13.8 Minimums and seeds

- **Minimums.** Validation: at least 100 pooled trades and 30 per instrument.
  Protocol B folds: at least 10 trades. Selection eligibility: per
  section 11.2.
- **Seeds.** `int(sha256(f"{config_hash}|{purpose}|{index}").hexdigest()[:16], 16)`,
  used with NumPy `Generator(PCG64)`. Algorithm and library versions are
  recorded in the registry.

### 13.9 Interpretation

- Not rejecting H0 is **not** evidence of no effect: interval widths and the
  minimum detectable mean at the observed variance are reported.
- Validation results are labelled "selection evidence on consulted data",
  never confirmatory.
- Profit factor never decides.
- One positive configuration is not success, and a negative first validation
  alone does not abandon Wave 3.

### 13.10 Acceptance for question C, per variant (Protocol A)

Each variant has a sensitivity standing:

| Variant | Parameter sensitivity | Cost and latency scenarios | Standing |
| --- | --- | --- | --- |
| H1-G | executed | executed | `SENSITIVITY_PASS` or `SENSITIVITY_FAIL` |
| H1-M | executed | executed | `SENSITIVITY_PASS` or `SENSITIVITY_FAIL` |
| H1-P, H1-PM | not executed | not executed | `SENSITIVITY_NOT_EVALUATED` |

H1-G or H1-M is `DEMONSTRATED FOR SELECTION — FINANCING EXCLUDED` only if all
of the following hold:

1. Holm rejection and adjusted lower bound greater than 0;
2. the minimums are met;
3. censoring ≤ 5 %;
4. `SENSITIVITY_PASS`: no sign reversal of the mean under the four ±20 %
   parameter perturbations;
5. the controls of section 13.7 pass.

The cost and latency scenarios are reported beside the result and do not
change the label.

**H1-P and H1-PM** can never reach `DEMONSTRATED FOR SELECTION`. When criteria
1, 2, 3, and 5 hold, they are labelled `COUNTERFACTUAL SIGNAL — SENSITIVITY NOT
EVALUATED`; otherwise `NOT DEMONSTRATED` or `INCONCLUSIVE`. They remain
research counterfactuals in every case.

Protocol B consistency (a positive mean in at least half of the folds) is
reported alongside.

### 13.11 Bootstrap and statistic edge cases (QG-18)

| Case | Deterministic handling | Effect |
| --- | --- | --- |
| Resample with zero trades | the replicate is `INVALID` and excluded from percentiles and p-values | counted in the valid-replicate check |
| Fewer than 9,900 valid replicates of 10,000 | bootstrap `INSUFFICIENT` | variant `INCONCLUSIVE`; Holm p = 1 |
| Zero variance of trade R (all equal) | sample `DEGENERATE` | variant `INCONCLUSIVE`; Holm p = 1 |
| Undefined studentized statistic (zero bootstrap standard error) | the configuration is `UNDEFINED` in Romano–Wolf and excluded from its maximum statistic | reported; Romano–Wolf is exploratory |
| Undefined Sharpe ratio (fewer than 2 trades or zero deviation) | Deflated Sharpe `UNDEFINED` | reported; never decisive |
| No eligible configuration in Protocol A selection | `NO_ELIGIBLE_CONFIGURATION` | variant `INCONCLUSIVE`; Holm p = 1 |
| Validation minimums not met | `INCONCLUSIVE` | Holm p = 1 |

The Holm family always contains the four variants (m = 4). A failed,
degenerate, or inconclusive variant enters with p = 1 and is never removed.
Equal p-values are ordered H1-G, H1-P, H1-M, H1-PM.

### 13.12 Void runs

A run is void if it has:

- any prefix-invariance violation (at least 200 seeded checkpoints plus every
  month boundary);
- any refused-partition read, or a missing ledger record;
- an integrity failure;
- an unregistered configuration;
- a non-deterministic rerun;
- an unrecorded code SHA or dirty tree.

## 14. Architecture and file ownership

The harness imports `research.datasets` and `research.elliott_causal`
read-only; it introduces no production framework. NumPy and SciPy come from
the existing requirements.

| Path | Responsibility |
| --- | --- |
| `research/harness/partitions.py` | section 5 tables, `H_END`, refusals |
| `research/harness/data.py` | registry verification, ledger-first reads, monthly assembly, gates |
| `research/harness/config.py` | configurations, hashes, budget counter (section 12) |
| `research/harness/signals.py` | causal signals, timeline, status ladder |
| `research/harness/execution.py` | tick simulator, precedence (section 10.4), boundaries |
| `research/harness/costs.py` | section 10.2 |
| `research/harness/a07_bridge.py` | frozen A07 E07 RR in-process, or the labelled fallback |
| `research/harness/protocols.py` | Protocols A and B, selection, purging |
| `research/harness/metrics.py` | attribution, fill rates, R, censoring |
| `research/harness/stats.py` | section 13 |
| `research/harness/controls.py` | section 13.7 |
| `research/harness/registry.py` | append-only experiment registry |
| `research/harness/report.py`, `cli.py`, `__main__.py` | deterministic reports and commands |
| `research/experiments/registry.jsonl` | committed registry |
| `research/tests/test_q00_*.py` | Q00 tests |
| `docs/project/P04_R01_Q00_PROTOCOL.md` | pre-registration record |

D-family and workflow files belong to D01, D02, and CI00. Any change to
`research/elliott_causal/**` needs its own authorization.

## 15. QA acceptance matrix

| # | Requirement | Future test (I00 unless noted) |
| --- | --- | --- |
| 1 | Dataset integrity, manifest tampering | `test_q00_refuses_tampered_or_unverified_manifests` |
| 2 | Source-side prices | `test_q00_buy_ask_entry_bid_exits_and_sell_mirror` |
| 3 | No future information | `test_q00_prefix_invariance_checkpoints_and_month_boundaries` |
| 4 | No premature entry | `test_q00_no_order_before_t_submit` |
| 5 | No look-ahead fills | `test_q00_look_ahead_control_is_flagged` |
| 6 | Order expiry | `test_q00_limit_expiry_inclusive_at_300s` |
| 7 | Missing ticks | `test_q00_pending_or_open_lifetime_touching_gap_is_data_incomplete` |
| 8 | Price gaps | `test_q00_stop_fills_at_gap_tick_with_adverse_slippage` |
| 9 | Stop before target | `test_q00_same_group_stop_wins` |
| 10 | OOS access denial | `test_q00_quarantined_intermediate_and_final_oos_refused` |
| 11 | Pre-registration | `test_q00_unregistered_configuration_is_void` |
| 12 | Multiple testing | `test_q00_holm_procedure_and_adjusted_bounds_on_fixtures` |
| 13 | Determinism | `test_q00_identical_reports_on_rerun` |
| 14 | Frozen isolation | `test_q00_no_production_patch_and_identities_unchanged` |
| 15 | FAITHFUL versus PRIMARY_ONLY | `test_q00_paired_comparison_uses_identical_resamples` |
| 16 | Time-validity attribution | `test_q00_each_primary_has_exactly_one_class` |
| 17 | RR ownership | `test_q00_rr_frozen_a07_or_labelled_non_governed` |
| 18 | Windows and Research CI repeatability | owner run plus CI on the exact SHA |
| 19 | Batch reproducibility (D01) | fresh-root rebuild reproduces every `dataset_id` |
| 20 | Holiday calendar (D01) | `test_d01_holiday_hours_are_expected_closures` |
| 21 | Future OOS versus quarantine | `test_q00_forward_data_before_f_star_is_never_final_oos` |
| 22 | Partition boundaries | `test_q00_partition_table_boundaries_are_half_open_utc` |
| 23 | No validation access from development | `test_q00_development_run_cannot_read_validation_ticks` |
| 24 | Censoring sensitivity | `test_q00_censored_mark_to_market_and_sensitivities_reported` |
| 25 | Fixed versus adaptive | `test_q00_protocol_a_selection_frozen_before_validation_read` |
| 26 | Budget enforcement | `test_q00_budget_refuses_the_51st_h1_configuration` |
| 27 | Full profile versus partial | `test_q00_every_primary_carries_full_profile_not_evaluated` |
| 28 | Confidence gate preservation | `test_q00_no_fabricated_probability_or_confidence` |
| 29 | Pending invalidation | `test_q00_stop_cross_cancels_pending_order` |
| 30 | Same-group entry and stop | `test_q00_entry_and_stop_in_one_group_is_invalidated` |
| 31 | Event precedence | `test_q00_precedence_table_property_test` |
| 32 | C1 Level 1 data equivalence (D01-P) | `test_d01_alternative_export_equals_bi5_ticks` |
| 33 | Statistical correctness | `test_q00_bootstrap_holm_dsr_romano_wolf_reference_values` |
| 34 | Planned versus executed RR and R | `test_q00_rr_uses_planned_entry_and_r_uses_executed_risk` |
| 35 | No double-counted costs | `test_q00_spread_slippage_commission_counted_once_buy_and_sell` |
| 36 | Sensitivity standing | `test_q00_primary_only_variants_never_get_sensitivity_pass` |
| 37 | Rounding and deduplication | `test_q00_sensitivity_rounding_and_identity_deduplication` |
| 38 | Bootstrap edge cases | `test_q00_zero_trade_resamples_degenerate_and_undefined_statistics` |
| 39 | Fixed Holm family | `test_q00_inconclusive_variant_stays_in_holm_with_p_one` |
| 40 | Financing label | `test_q00_every_economic_result_is_financing_excluded` |
| 41 | C1 Level 2 behavioural equivalence (after I00) | `test_q00_alternative_source_reproduces_execution_reports` |

```gherkin
Scenario: Quarantine and intermediate data
  Given a request for XAUUSD 2023 or EURUSD 2024 data
  Then the harness refuses it before any ledger record or content read

Scenario: Forward data before the final freeze
  Given data timestamped after H_END but before F_STAR
  Then it is UNVERIFIED_INTERMEDIATE and never FINAL_OOS

Scenario: Development cannot peek at validation
  Given a development position open at 2019-01-01
  Then it is CENSORED at the last development quote
  And no validation tick is read

Scenario: Validation sealed
  Given no committed Protocol A selection record
  Then validation acquisition and reads are refused

Scenario: No fill through an invalidated setup
  Given a pending BUY limit
  When one tick group crosses both the limit and the stop
  Then the outcome is INVALIDATED_BEFORE_FILL and no trade exists

Scenario: Budget ceiling
  Given 50 registered H1 configurations
  When a 51st is requested
  Then registration is refused

Scenario: Executed risk denominator
  Given a market BUY whose fill slips above the planned entry
  Then A07 RR is evaluated at the planned entry
  And the primary research R divides by the executed entry-to-stop distance
  And slippage is counted once

Scenario: Counterfactual sensitivity
  Given an H1-P result meeting every other acceptance criterion
  Then its label is COUNTERFACTUAL SIGNAL — SENSITIVITY NOT EVALUATED

Scenario: Inconclusive variant in the Holm family
  Given a variant with no eligible configuration
  Then it enters the four-member Holm family with p = 1

Scenario: Partial profile labelling
  Given any H1-G result
  Then it carries FULL_PROFILE_NOT_EVALUATED and CONFIDENCE_UNCALIBRATED
  And no probability or confidence value is fabricated
```

## 16. Research CI amendment (Q00-CI00)

The gap is open. The authorized change to `.github/workflows/research.yml`
is exactly the following, with every other line unchanged:

```yaml
      - name: Black
        run: python -m black --check research/datasets research/elliott_causal research/tests

      - name: Ruff
        run: python -m ruff check research/datasets research/elliott_causal research/tests

      - name: MyPy
        run: >-
          python -m mypy --explicit-package-bases
          research/datasets research/elliott_causal research/tests

      - name: Research tests and coverage
        run: >-
          python -m pytest -p no:cacheprovider research/tests
          --cov=research/datasets --cov=research/elliott_causal
          --cov-report=term-missing

      - name: Per-package coverage gates
        run: |
          python -m coverage report --include="*/research/datasets/*" --fail-under=95
          python -m coverage report --include="*/research/elliott_causal/*" --fail-under=95
```

Compatibility:

- `pytest-cov` (which brings `coverage`) is in the `dev` extra the workflow
  installs.
- The repository defines no coverage configuration, so the default `.coverage`
  data file in the working directory is used.
- Wildcard-prefixed patterns match absolute recorded paths.

**Pending validation:** these commands have not been executed, because the
governance environment lacks `pytest-cov`. CI00 closes only when they pass in
Research CI on its exact SHA.

Adding `research/harness` to these steps is part of the Q00-I00
authorization, which must name the workflow.

## 17. Milestones and dependencies

| Milestone | Depends on | Scope | Network |
| --- | --- | --- | --- |
| P04-R01-Q00-G00 | E00 | this record, ROADMAP | none |
| P04-R01-Q00-CI00 | Q00-G00 | workflow (section 16), CI00 closure record, ROADMAP | none |
| P04-R01-D01-B1 | Q00-G00, CI00 closed | `research/datasets/**`, manifests, `research/tests/**`, D01 closure, ROADMAP | owner-run, 2018-01 to 2018-06 |
| P04-R01-D01-P (optional) | D01-B1 | C1 export probe, Level 1 equivalence, A01 amendment proposal | owner-run, D00 week plus one B1 month |
| P04-R01-D01-B2… | D01-B1; C1-sourced batches also need D01-P Level 1, an A01 amendment, and Level 2 before use in V00 | further development batches | owner-run, per authorization |
| P04-R01-Q00-I00 | CI00, D01-B1 (later development batches may still be pending) | section 14, harness CI extension, pre-registration record; Level 2 test when D01-P exists | none |
| P04-R01-Q00-V00 | I00 and **all authorized development datasets** | Protocol A selection, development diagnostics | none |
| P04-R01-D02 | committed V00 selection record | validation data, 2019–2021 | owner-run |
| P04-R01-Q00-V01 | D02 | Protocol A validation, then Protocol B | none |
| P04-R01-Q00-R00 | V01 | results review, Q00 closure | none |
| P04-R01-C00 | R00 | decision A, B, or C | none |
| `F_STAR` freeze, FINAL_OOS collection, FINAL_OOS evaluation | C00 decision A | separate future milestones | not authorized |

No milestone implicitly authorizes the next.

## 18. Risks

| Risk | Mitigation |
| --- | --- |
| Acquisition throughput | measured by B1; C1 probe (Level 1, then Level 2 after I00); any coverage reduction only by amendment |
| Financing excluded from economics | `FINANCING_EXCLUDED` label; rollover exposure reported; model only by amendment |
| Frozen 300 s expiry yields almost no fills (prior probes: −0.17 R with a 24-bar limit; RR ≥ 3 rejected 596 of 598 market entries) | measured as question B; deferred to C00 |
| Partial-profile results mistaken for the full profile | mandatory status ladder (section 7.3) |
| A07 not invocable without F02 | I00 proof; `RR_NON_GOVERNED` fallback |
| Contaminated validation | reduced standing; separate reporting; no confirmation claim |
| Budget at exactly 50 | no reserve; amendment required |
| Unpinned lint tools | CI00 records versions; failures are fixed, not waived |

## 19. Closure gates of this milestone

1. Owner publication authorization of this text.
2. One atomic commit of this record and the ROADMAP rows. ROADMAP entries:
   - Q00-G00: CLOSED / FROZEN;
   - Q00-CI00: READY FOR AUTHORIZATION REVIEW;
   - D01-B1: READY FOR AUTHORIZATION REVIEW, subject to CI00 closure;
   - D01-P, D01-B2 and later, Q00-I00, Q00-V00, D02, Q00-V01, Q00-R00, C00,
     `F_STAR`, FINAL_OOS collection and evaluation, P04-F02 to F04, P05, and
     demo or live trading: NOT AUTHORIZED.
3. Markdownlint, MkDocs strict, and `git diff --check` pass.
4. Collection 3127 and compliance 612 with the unchanged digest; no change
   under `epip/`, workflows, or research code.
5. Quality, CodeQL, and Documentation pass on the exact SHA. Research does not
   trigger for a documentation-only change, and that is stated, not claimed.

## 20. C00 decision prerequisites

C00 may decide only with all of the following in hand:

- the answers to A, B, and C per H1 variant, with intervals, status labels, and
  sensitivity standing;
- the financing exposure (rollovers and weekends crossed) behind
  `FINANCING_EXCLUDED`;
- Protocol A and Protocol B results kept separate;
- the alternates consequences;
- the temporal attribution;
- the A07 RR status;
- the partial-profile limitations;
- the contamination statement;
- censoring rates;
- a complete registry and ledger;
- the control outcomes.

C00 records G00 decision A, B, or C. No outcome authorizes demo or live
trading, and FINAL_OOS requires its own milestones after `F_STAR`.
