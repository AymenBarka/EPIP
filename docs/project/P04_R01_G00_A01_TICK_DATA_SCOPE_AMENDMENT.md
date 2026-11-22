# P04-R01-G00-A01 — Tick-Level BID/ASK Historical Data Scope Amendment

Status: **CLOSED / FROZEN** upon publication, subject to exact-final-commit
publication gates

Scope: amendment of the historical dataset scope of P04-R01-G00 only; no
implementation, no data acquisition

## 1. Authority and amended sections

This amendment is explicitly authorized by the owner. It amends
[P04-R01-G00](P04_R01_G00_RESEARCH_GOVERNANCE_AND_CAUSAL_ELLIOTT_READINESS.md)
only where stated below:

| G00 section | Amendment |
| --- | --- |
| 7.2 Scope | Replaced by section 3 of this record |
| 7.3 Canonical format | Extended by sections 5 and 8 for tick data |
| 8 Data provenance and reproducibility | Extended by section 8 (raw versus canonical checksums) |
| 19 D00 authorization boundary | Objective and success criteria extended by sections 6, 7, and 9 |

Every other G00 section remains in force unchanged, including the five owner
decisions D1–D5, the consultation ledger, the Research CI contract, and the
prohibitions. This amendment changes no production code, frozen contract,
identity, fingerprint, test, or compliance baseline.

The owner's need is realistic research and future backtests that respect
intrabar order. Hourly candles cannot provide that order; BID/ASK ticks can.

## 2. Provider roles

| Role | Source | Use |
| --- | --- | --- |
| Primary | Dukascopy tick BID/ASK hourly files (`{HH}h_ticks.bi5`) | canonical research ticks for EURUSD and XAUUSD |
| Cross-check | Dukascopy H1 BID and ASK candle files (`BID_candles_hour_1.bi5`, `ASK_candles_hour_1.bi5`) | independent verification of tick-derived H1 bars |
| Independent comparison | MetaTrader 5 Admirals exports (bars and ticks) | provider-difference analysis |

Prices from different providers are **never merged**, averaged, or substituted
for one another, silently or otherwise. Every dataset carries exactly one
provider identity, and comparisons are reported as differences between
separately identified datasets.

Pre-acquisition audit facts recorded on 2026-11-22 by HTTP `HEAD` requests
only (no content downloaded):

- tick hour files exist for EURUSD and XAUUSD from 2003 through October 2026;
  XAUUSD files in 2003 are near-empty, and 2008 files are regular;
- H1 BID and ASK monthly candle files exist for both instruments;
- an hour without quotes returns HTTP 200 with zero bytes, which must be
  distinguished from a failed request;
- the endpoint is undocumented and throttles bursts of about 100 requests
  (HTTP 503 observed during the audit).

## 3. Amended dataset scope (replaces G00 section 7.2)

- **Instruments in initial acquisition:** EURUSD and XAUUSD only.
- **Primary granularity:** BID/ASK ticks.
- **Derived granularity:** H1 and H4 bars built from ticks (section 4).
- **Cross-check granularity:** Dukascopy H1 BID and ASK candles.
- **Excluded from initial acquisition:** GBPUSD and USDJPY. Their ledger status
  remains `UNVERIFIED — NOT ATTESTED VIRGIN` for GBPUSD and `CONSULTED` for
  USDJPY, as recorded in G00 section 10.
- **Full-history acquisition:** not authorized. Any extension beyond the
  technical sample of section 6 requires separate authorization.

## 4. Deterministic bar derivation from ticks

- Bars use half-open UTC intervals `[start, end)`. H1 intervals start on whole
  UTC hours. H4 intervals start at 00:00, 04:00, 08:00, 12:00, 16:00, and
  20:00 UTC.
- BID bars are built from BID prices only and ASK bars from ASK prices only.
  MID is never substituted for BID or ASK.
- Open is the first tick, close the last tick, and high and low the extremes
  inside the interval, in source order with a deterministic tie rule for
  identical timestamps (original record order).
- An interval without ticks produces **no bar**. No tick, price, or bar is
  invented, carried forward, or interpolated.
- An interval whose underlying source hours are not all present is emitted
  only with an explicit `INCOMPLETE` quality flag, or withheld, as D00
  specifies; it is never presented as complete.
- Each bar records its tick count. Dukascopy BID and ASK quoted volumes are
  stored as separate quoted-volume fields and are never summed into, or
  presented as, executed trade volume.

## 5. Tick representation rules

- Timestamps are UTC with millisecond resolution, derived from the hour-file
  path plus the record's millisecond offset.
- Prices are stored as integer points with a declared per-instrument scale;
  no floating-point rounding enters content identity.
- Records keep source order; duplicates and non-monotonic timestamps are
  detected and reported, never silently dropped or reordered.
- A record with `ask < bid`, a non-positive price, or a malformed length fails
  validation closed.

## 6. First technical sample

| Item | Value |
| --- | --- |
| Instruments | EURUSD, XAUUSD |
| Ticks | from 2012-03-12 00:00 UTC to 2012-03-17 00:00 UTC, end excluded |
| Cross-check candles | H1 BID and ASK, March 2012 (Dukascopy month directory `2012/02`, zero-based) |
| Download ceiling | 20 MB of compressed bytes, with a hard stop before the ceiling is exceeded |
| Executor | owner-run Python script on Windows (G00 decision D2) |

Ledger classification: the sample lies in periods already recorded as
consulted for EURUSD (2010–2018) and in a period of unknown prior consultation
for XAUUSD. It is a **technical** sample: it may be used to validate the
pipeline, never to evaluate a strategy, and it consumes no OOS candidate.

## 7. Acquisition conduct

- No download occurs during A01.
- Before the first acquisition, D00 records the provider terms of use that
  apply to the endpoint, or the absence of explicit terms, and the owner
  confirms that local research use is acceptable.
- D00 fixes, within these limits, the exact request policy: sequential
  requests, at most one request per second, exponential backoff on HTTP 429 or
  503, a bounded retry count, and an abort when the byte ceiling or a
  consecutive-failure limit is reached.
- Every request, response status, byte count, and retry is logged as
  acquisition metadata, separate from content identity.

## 8. Raw and canonical identity (extends G00 sections 7.3 and 8)

- Original `.bi5` files are retained byte-for-byte, never modified.
- The manifest records **two** distinct SHA-256 values per file: the raw
  downloaded bytes, and the canonical decompressed representation.
- Normalized data may be stored as deterministic gzip-compressed CSV. D00 must
  define the column order, numeric representation, row order, line endings,
  UTF-8 encoding, header, gzip header fields (fixed modification time and no
  file name), and compression level, so that identical inputs yield identical
  bytes.
- Content identity uses the canonical uncompressed representation, so that it
  does not depend on the compressor implementation.

## 9. Storage and redistribution

- All acquired and derived data stays under repository-root `data/`, excluded
  from Git, as decided in G00 D1.
- No redistribution of provider data is authorized, inside or outside the
  repository.
- Only manifests, schemas, acquisition code, and small synthetic fixtures are
  versioned.

## 10. Use restriction for future milestones

For any future backtest or execution simulation that depends on intrabar
order, OHLC bars (provider candles or tick-derived bars) **cannot replace**
BID/ASK ticks. Q00 inherits this rule as a blocking validation criterion.

## 11. Acceptance scenarios

```gherkin
Scenario: Empty hour is not a failure
  Given a tick hour file returned with HTTP 200 and zero bytes
  Then the hour is recorded as NO_QUOTES
  And no bar is created for it

Scenario: No synthetic bar
  Given an H1 interval without ticks
  Then no H1 bar exists for that interval

Scenario: Separate sides
  Given ticks for an interval
  Then BID bars use only BID prices and ASK bars use only ASK prices

Scenario: Provider separation
  Given a Dukascopy dataset and an MT5 dataset for the same period
  Then each keeps its own provider identity and no price is merged

Scenario: Download ceiling
  Given the 20 MB ceiling
  When the next file would exceed it
  Then acquisition stops before downloading that file

Scenario: Dual checksum
  Given an acquired tick file
  Then the manifest holds the raw SHA-256 and the canonical SHA-256
  And a rebuild from raw bytes reproduces the canonical SHA-256
```

## 12. Resulting milestone state

| Milestone | State |
| --- | --- |
| P04-R01-G00 | CLOSED / FROZEN |
| P04-R01-G00-A01 | CLOSED / FROZEN |
| P04-R01-D00 | AUTHORIZED / READY FOR IMPLEMENTATION, under G00 as amended here |
| P04-R01-E00 / Q00 / C00 | NOT AUTHORIZED |
| P04-F02 | NOT AUTHORIZED / RESEARCH RECONCILIATION REQUIRED |
| P04-F03 / P04-F04 / P05 | NOT AUTHORIZED |

D00 is not started by this record.
