# P04-R01-D00 — Reproducible Tick-Level BID/ASK Dataset Foundation

Status: **CLOSED / FROZEN**

D00 closed on 2026-11-24 after the owner-run acquisition of the authorized
technical sample and the validation steps of section 15; section 19 records
the evidence and the registered dataset identities.

## 1. Authority and scope

Implemented under
[P04-R01-G00](P04_R01_G00_RESEARCH_GOVERNANCE_AND_CAUSAL_ELLIOTT_READINESS.md)
as amended by
[P04-R01-G00-A01](P04_R01_G00_A01_TICK_DATA_SCOPE_AMENDMENT.md), starting from
`4bac84c446907f5833f996848ed9e0fa43a0b8fb`. The file scope is G00 section 17:

| Path | Purpose |
| --- | --- |
| `research/datasets/**` | research-only dataset package (15 modules) |
| `research/tests/**` | offline tests and fixtures (164 test nodes) |
| `.gitignore` | adds `/data/` only |
| `.github/workflows/research.yml` | Research CI, explicitly named by the D00 authorization |
| `docs/project/P04_R01_D00_DATASET_CLOSURE.md` | this record |
| `docs/project/ROADMAP.md` | D00 status |

No file under `epip/` or `tests/` changes, and `research/__init__.py` is not
needed (`research` is a namespace package). No production module imports
`research`, and the research package imports nothing from `epip`.

## 2. Architecture

```text
Dukascopy tick and H1 candle files ──► acquisition (bounded, journaled, atomic)
                                            │ immutable raw .bi5 under data/raw
                                            ▼
                     decode + validate (fail closed) ──► canonical tick CSV (gzip)
                                            │
                     H1 / H4 BID and ASK bars (half-open UTC) ──► bar CSV (gzip)
                                            │
          Dukascopy H1 candles ──► independent cross-check report (xcheck-h1/1)
                                            │
                raw + canonical SHA-256 manifests ──► local registry
                                            │
                 consultation ledger ──► future E00 / Q00 consumers

MT5 bar/tick exports ──► separate importer ──► own manifests (never merged)
```

| Module | Responsibility |
| --- | --- |
| `contracts.py` | immutable typed contracts, enums, versions, fail-closed errors |
| `dukascopy.py` | instrument scales, `.bi5` tick and candle decoding, URLs, paths, empty-hour calendar |
| `canonical.py` | frozen CSV encoding, parsing, deterministic gzip, SHA-256 |
| `aggregate.py` | H1/H4 bar derivation per side |
| `crosscheck.py` | derived H1 versus provider H1 comparison |
| `mt5.py` | MT5 bar/tick import with explicit server-time convention |
| `manifest.py` | deterministic manifests, identity, tamper and file verification |
| `registry.py` | local manifest-based registry |
| `ledger.py` | consultation ledger and conservative OOS status |
| `acquisition.py` | authorized windows, plan, transport, limits, journal, resume |
| `build.py` | offline build from raw files to registered datasets |
| `storage.py` | storage convention, safe relative paths, atomic writes |
| `cli.py`, `__main__.py` | Windows-compatible command line |

## 3. Dataset schemas and versions

| Contract | Version |
| --- | --- |
| Manifest schema | `1` (any other version is rejected) |
| Tick CSV | `epip-research-ticks-csv/1` |
| Bar CSV | `epip-research-bars-csv/1` |
| MT5 CSV | `epip-research-mt5-csv/1` |
| Cross-check policy | `xcheck-h1/1` |
| Empty-hour calendar | `ny-1700-close/1` (recorded as a `SESSION_CALENDAR` diagnostic in tick and bar manifests) |

Contracts carry provider identity, instrument with explicit price decimals,
price side (BID or ASK, never MID), granularity (TICK, H1, H4), source format,
coverage, raw artifact identity, canonical content identity, diagnostics, and
lineage. Ticks hold integer points and quoted volumes in integer millionths.
Bars hold one side, OHLC points, contributing tick count, and a
COMPLETE/INCOMPLETE coverage flag. There is no trade-volume field: Dukascopy
volumes are quoted liquidity.

## 4. Source-specific decoding

Verified Dukascopy formats (LZMA "alone" streams, big-endian):

- tick hour file: 20-byte records `uint32 ms offset, uint32 ask, uint32 bid,
  float32 ask volume, float32 bid volume`, offset from the UTC hour start;
- H1 candle month file: 24-byte records `uint32 second offset, uint32 open,
  uint32 close, uint32 low, uint32 high, float32 volume`.

Scales are configured per instrument: EURUSD 5 decimals, XAUUSD 3 decimals.
Any other instrument is rejected. Decoding fails closed on invalid LZMA, a
record length not a multiple of the record size, offsets outside the UTC hour
or month, non-positive prices, ask below bid, non-finite or negative volumes,
out-of-order records, and exact duplicate consecutive records. Distinct quotes
in the same millisecond are kept in source order. Candles must sit on hour
boundaries, be strictly increasing, and satisfy OHLC invariants.

## 5. Normalization specification

- UTF-8, `\n` line endings, header row, final newline, no trailing spaces.
- Tick columns: `timestamp_utc,bid,ask,bid_volume,ask_volume`.
- Bar columns: `start_utc,end_utc,side,open,high,low,close,tick_count,coverage`.
- Timestamps: `YYYY-MM-DDTHH:MM:SS.mmmZ`.
- Prices: integer points rendered with exactly the instrument's decimals;
  volumes with exactly six decimals. No floating-point formatting.
- Row order: ticks in source order; bars by start, then side.
- Duplicate policy: exact duplicate consecutive tick records reject the file.
- Invalid tick policy: any invalid record rejects the whole hour file
  (`CORRUPTED`); nothing is repaired, dropped, or interpolated.
- gzip: level 9, `mtime=0`, empty file name.

## 6. Hashing rules

| Digest | Input |
| --- | --- |
| `raw_sha256` | exact provider bytes as downloaded |
| `canonical_sha256` | uncompressed canonical CSV bytes (authoritative content identity) |
| `compressed_sha256` | stored gzip bytes |
| `dataset_id` | canonical JSON of the manifest identity section |

The manifest's `provenance` section (builder, broker, convention source)
never participates in `dataset_id`. Acquisition timestamps live only in the
journal.

## 7. H1/H4 derivation

Bars are half-open UTC intervals `[start, end)`; a tick exactly on a boundary
belongs to the next interval. H4 intervals start at 00, 04, 08, 12, 16, and
20 UTC. BID and ASK bars are built independently. An interval without ticks
produces no bar. A bar is COMPLETE only if every source hour it spans is
POPULATED or an EXPECTED_CLOSURE; otherwise it is INCOMPLETE. Tick count is
the number of contributing records. Bar datasets record the tick dataset in
their lineage.

## 8. Independent H1 cross-check

Policy `xcheck-h1/1` compares tick-derived H1 bars with Dukascopy H1 candles
inside the tick window, with a tolerance of 0 points per field. Justification:
both come from the same provider quote stream, so any difference is a finding.
The report lists compared and matched bars, field deviations, bars missing on
either side, provider zero-volume filler candles, and INCOMPLETE derived bars.
Status is `CONSISTENT` or `DEVIATIONS_REPORTED`. Derived values are never
altered to match the provider.

## 9. MT5 import limitations

- Supported: Symbols-window exports of bars and ticks, tab or comma separated,
  UTF-8, UTF-8 with BOM, or UTF-16.
- Broker server time is converted only through an explicit
  `ServerTimeConvention` (a fixed offset with documented evidence, or a table
  of UTC-anchored offset segments). Without one, the import is rejected
  (quarantined). Ambiguous or non-existent local times at offset changes are
  rejected.
- A missing BID or ASK in a tick row stays missing. ASK is never reconstructed
  from BID and spread. Bar price side must be declared. Spread is kept as
  published.
- No terminal, broker connection, or MT5 package is used.

## 10. Manifest and registry usage

`registry/<dataset_id>.json` stores canonical manifest bytes. Registration
first re-verifies every referenced file. It is idempotent for identical bytes
(`duplicate`) and rejects any other content under the same identity
(collision). Listing, inspection, and resolution (by identity or a unique
prefix of at least 8 hex characters) re-validate each manifest. `verify` also
re-hashes raw and canonical files.

## 11. Data-quality classifications

| Status | Meaning |
| --- | --- |
| POPULATED | non-empty, decoded, validated |
| EXPECTED_CLOSURE | HTTP 200 with zero bytes for an hour wholly inside a scheduled closure |
| EMPTY_UNEXPLAINED | HTTP 200 with zero bytes for any other hour |
| MISSING | HTTP 404 |
| THROTTLED | HTTP 429 or 503 after bounded retries |
| PROVIDER_ERROR | other HTTP error or transport failure after retries |
| CORRUPTED | payload failed decoding or validation after retries |
| PARTIAL | body shorter than the declared length after retries |
| NOT_ACQUIRED | no journal record |

An empty response is never a closure by itself. Calendar `ny-1700-close/1`
schedules a closure from Friday 17:00 to Sunday 17:00 New York time for every
instrument and, for XAUUSD only, a daily break from 17:00 to 18:00 New York
time Monday to Thursday. New York time follows the United States rule in force
since 2007 (second Sunday of March 07:00 UTC to first Sunday of November
06:00 UTC); outside 2007–2099 the calendar refuses to classify. Holidays are
not modelled, so an empty holiday hour stays EMPTY_UNEXPLAINED and its bars
INCOMPLETE.

The journal keeps what was observed (an empty HTTP 200). `build` derives the
classification from the calendar at build time, so a journal written under the
former `saturday-only/1` calendar is reinterpreted, never rewritten.

## 12. OOS ledger

`ledger.py` reproduces the G00 section 10 baseline: EURUSD, XAUUSD, and USDJPY
are CONSULTED; GBPUSD is `UNVERIFIED — NOT ATTESTED VIRGIN`. ATTESTED_VIRGIN
requires an explicit owner attestation and is impossible for a CONSULTED
instrument. The append-only consultation ledger records dataset identity and
digest, experiment ID, purpose, UTC timestamp, partition (TECHNICAL,
DEVELOPMENT, VALIDATION, FINAL_OOS), and outputs. No experiment was run and no
consultation was recorded during D00.

## 13. Research CI

`.github/workflows/research.yml` runs on pushes and pull requests touching
`research/**`, the workflow, `pyproject.toml`, or `requirements.txt`. With
Python 3.13 and `PYTHONHASHSEED=0` it runs Black, Ruff, strict MyPy, the
research tests with `--cov=research/datasets --cov-fail-under=95`, a second
identical test run, and a production-isolation guard failing any research push
that modifies `epip/`. It uses no network data, MT5, broker, secret, or large
dataset. The Quality, CodeQL, and Documentation workflows are unchanged.

## 14. Test evidence and reproducibility proof

| Gate | Result |
| --- | --- |
| Research tests | 164 passed (101 test functions) |
| Research coverage | 100.00 % of 2,071 statement lines (local standard-library line tracer); CI enforces ≥ 95 % with pytest-cov |
| Research static checks | Black, Ruff, strict MyPy: pass (23 files) |
| Canonical collection | 3127 before and after; 0 predecessor nodes removed |
| Canonical regression | 3126 passed, 1 deselected; stress test passed separately |
| Production static checks | Black (694 files), Ruff, strict MyPy (694 files): pass |
| Compliance | inventory 612, digest `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1`, unchanged |

Reproducibility proof (`test_rebuild_is_reproducible_bit_for_bit`): the same
raw files built in two separate roots with different provenance produce
identical dataset identities and byte-identical canonical gzip files, and a
rebuild in place is idempotent.

Acceptance mapping (prefixes: K `test_d00_dukascopy.py`, C
`test_d00_canonical_aggregate.py`, M `test_d00_mt5.py`, R
`test_d00_manifest_registry_ledger.py`, A `test_d00_acquisition.py`, P
`test_d00_pipeline_cli_isolation.py`):

| # | Requirement | Executed tests |
| --- | --- | --- |
| 1 | Valid tick decoding | K `test_valid_tick_decoding_maps_offsets_prices_and_volumes` |
| 2 | Invalid record length | K `test_invalid_record_length_fails_closed` |
| 3 | Invalid LZMA payload | K `test_invalid_lzma_payload_fails_closed` |
| 4 | Instrument-specific scaling | K `test_instrument_specific_scaling_is_explicit`; C `test_xauusd_prices_render_with_three_decimals` |
| 5 | UTC timestamp boundaries | K `test_offsets_outside_the_utc_hour_fail`, `test_last_millisecond_of_hour_is_inside`, `test_hour_start_must_be_aligned` |
| 6 | BID/ASK consistency | K `test_ask_below_bid_fails_closed`, `test_equal_bid_ask_is_accepted` |
| 7 | Invalid prices | K `test_invalid_prices_and_volumes_fail_closed` |
| 8 | Duplicate ticks | K `test_duplicate_tick_fails_closed`, `test_same_millisecond_distinct_quotes_are_kept_in_source_order` |
| 9 | Out-of-order ticks | K `test_out_of_order_ticks_fail_closed` |
| 10 | Canonical serialization determinism | C `test_canonical_tick_csv_is_frozen_and_round_trips`, `test_serialization_is_deterministic_and_checksums_stable`, `test_property_seeded_random_ticks_round_trip` |
| 11 | Raw checksum stability | C `test_serialization_is_deterministic_and_checksums_stable`; R `test_file_tampering_is_detected` |
| 12 | Canonical checksum stability | P `test_rebuild_is_reproducible_bit_for_bit` |
| 13 | Gzip determinism | C `test_gzip_is_deterministic_with_zero_mtime_and_no_name` |
| 14 | H1 aggregation | C `test_h1_aggregation_per_side_with_tick_counts`, `test_tick_on_boundary_belongs_to_next_interval` |
| 15 | H4 aggregation | C `test_h4_aggregation_spans_four_hours` |
| 16 | Empty intervals | C `test_empty_interval_produces_no_bar` |
| 17 | Incomplete intervals | C `test_incomplete_coverage_is_flagged_not_hidden`; P `test_incomplete_hours_are_flagged_and_crosscheck_reports` |
| 18 | Independent H1 cross-check | C `test_crosscheck_consistent_when_provider_matches`, `test_crosscheck_reports_without_altering_values`; P `test_missing_hour_is_reported_on_both_sides` |
| 19 | MT5 tick import | M `test_mt5_tick_import_converts_server_time_and_keeps_missing_sides`, `test_mt5_tick_import_accepts_utf16_and_comma_exports` |
| 20 | MT5 bar import | M `test_mt5_bar_import_requires_declared_side_and_keeps_spread` |
| 21 | Ambiguous timezone rejection | M `test_ambiguous_timezone_is_rejected_quarantine`, `test_dst_overlap_is_ambiguous_and_gap_non_existent` |
| 22 | Manifest round-trip | R `test_manifest_round_trip_is_canonical`, `test_provenance_never_changes_identity` |
| 23 | Manifest tampering | R `test_manifest_tampering_is_detected`, `test_noncanonical_or_malformed_manifest_is_rejected`, `test_unsupported_manifest_version_is_rejected` |
| 24 | Registry collisions | R `test_registry_collision_and_corruption_are_rejected` |
| 25 | Registry integrity | R `test_registry_register_list_resolve_verify`, `test_registry_rejects_unverifiable_dataset`, `test_registry_reference_rules` |
| 26 | Offline dry-run | P `test_cli_plan_and_dry_run_are_offline` |
| 27 | Download budget | A `test_download_budget_is_never_exceeded`, `test_exhausted_budget_aborts_before_request`, `test_urllib_transport_contract_without_network` |
| 28 | Request-rate enforcement | A `test_minimum_interval_between_requests`, `test_request_ceiling_and_rate_are_enforced` |
| 29 | Bounded retries | A `test_bounded_retries_then_final_status`, `test_limits_validation_and_backoff_cap` |
| 30 | Empty HTTP response classification | A `test_empty_http_200_is_not_automatically_a_closure`; K `test_empty_hour_calendar_is_instrument_and_dst_aware`, `test_new_york_offset_follows_the_us_rule`; P `test_build_reclassifies_empty_hours_with_the_current_calendar` |
| 31 | Resume safety | A `test_resume_skips_verified_files_and_refuses_unverified`, `test_incomplete_read_is_a_transport_failure_not_a_crash`, `test_journal_records_the_last_error_detail`, `test_legacy_journal_lines_without_detail_are_read`; P `test_complete_rebuild_after_a_diagnostic_partial_build`, `test_cli_reports_pending_items_and_honours_options` |
| 32 | Atomic writes | A `test_atomic_write_never_overwrites_and_leaves_no_partial` |
| 33 | Consultation ledger | R `test_consultation_ledger_append_and_read`, `test_consultation_validation` |
| 34 | OOS status preservation | R `test_oos_status_is_preserved_and_never_inferred` |
| 35 | Frozen production-contract isolation | P `test_frozen_production_contract_isolation`, `test_network_is_forbidden_in_research_tests` |

Every research test runs with an autouse guard that makes socket connections
raise; all transports in tests are fakes.

## 15. Acquisition instructions (owner-run, separately authorized)

Preconditions:

1. Read and confirm the provider's terms of use for local research use
   (A01 section 7). Record the outcome in the D00 validation note.
2. Use Python 3.13 on Windows from the repository root.

```powershell
cd C:\Users\Ansible\Documents\GitHub\EPIP
python -m research.datasets plan --window A01-SAMPLE-2012-03
python -m research.datasets acquire --window A01-SAMPLE-2012-03 --dry-run
python -m research.datasets acquire --window A01-SAMPLE-2012-03 --confirm-provider-terms
# repeat the same acquire command until it prints ACQUISITION COMPLETE
python -m research.datasets build --window A01-SAMPLE-2012-03
python -m research.datasets registry list
python -m research.datasets registry verify <first 8+ hex of a dataset_id>
```

The only authorized window is `A01-SAMPLE-2012-03`: EURUSD and XAUUSD ticks
from 2012-03-12 00:00 UTC to 2012-03-17 00:00 UTC (end excluded) and H1 BID and
ASK candles of March 2012. Limits: 244 planned requests, at most 400 requests
including retries, at most 20,000,000 downloaded bytes, one request per second
minimum spacing, a per-request timeout of 30 seconds by default
(`--timeout-seconds`, 1 to 120), four retries with 2–60 second backoff, abort
after five consecutive failed files. The request ceiling applies to each run;
the byte ceiling of A01 section 7 is never exceeded by the whole sample. Each
failed item records the last error (`HTTP 503`, or the transport exception) in
the journal field `detail`.

At the end of every run the command lists the planned items not yet stored and
prints either `ACQUISITION COMPLETE` (exit code 0) or `ACQUISITION INCOMPLETE`
(exit code 2). Re-running resumes, skips verified files, and retries only the
pending items; an unverified existing file stops the run unless
`--allow-overwrite` is given.

`build` refuses to run while any planned item is pending. `--allow-incomplete`
produces a diagnostic build whose coverage states every gap; it never closes
D00. Canonical files and cross-check reports carry the first 16 hex digits of
their content digest in their name, so a complete build never collides with an
earlier diagnostic build.

Validation required for D00 closure:

1. acquisition reported `ACQUISITION COMPLETE`, within the byte budget;
2. `build` succeeded and `registry verify` passes for every dataset;
3. a second `build` from the same raw files, in a fresh data root, reproduces
   every `dataset_id`;
4. the cross-check reports are reviewed, and any deviation is explained;
5. the owner reports the dataset identities; a D00 closure update records them.

## 16. Instructions for future E00 consumers

- Resolve datasets only through the registry and verify them before use.
- Read canonical files only through `canonical.csv_to_ticks` and
  `csv_to_bars`.
- Respect coverage flags and hour classification; never fill gaps.
- Treat technical-sample datasets as `TECHNICAL`: no strategy evaluation.
- Record every consultation in the ledger before reading data.
- OHLC bars never replace ticks for intrabar-dependent simulation (A01
  section 10).

## 17. Known limitations

- Dukascopy's XAUUSD H1 candle feed is not an exact aggregation of its XAUUSD
  tick feed (section 19); provider candles remain a cross-check only.
- The empty-hour calendar does not model holidays or exceptional closures;
  such hours stay EMPTY_UNEXPLAINED.
- Exact duplicate consecutive ticks reject a whole hour file; if real data
  contains them, a governed policy change is required.
- The provider endpoint is undocumented; its terms must be confirmed by the
  owner before acquisition.
- Compressed digests depend on the zlib implementation; identity relies on the
  uncompressed canonical digest.
- MT5 conventions must be supplied by the owner from broker evidence; DST is
  supported only through an explicit offset table.
- The Research CI isolation guard fails any research push that also modifies
  `epip/`; such a change requires separate governance and a separate push.

## 18. Owner-run acquisition record and validation-phase corrections

The owner confirmed the provider terms and ran the acquisition of
`A01-SAMPLE-2012-03` on 2026-11-23 and 2026-11-24 (Windows, Python 3.13).
Observed behaviour of the endpoint and of the D00 tooling:

- The endpoint throttled heavily (HTTP 503) and dropped connections; most
  items needed several runs. After five runs, 239 of 244 items were stored
  (232 populated, 7 empty) and 5 XAUUSD hours of the London–New York overlap
  had failed every attempt (13 March 13h, 15 March 10h and 12h, 16 March 10h
  and 12h UTC).
- The seven empty hours are all scheduled closures: EURUSD Friday 16 March
  21h–23h UTC, XAUUSD Friday 21h–23h UTC, and XAUUSD Wednesday 14 March 21h UTC
  (the daily metals break). The former `saturday-only/1` calendar classified
  them EMPTY_UNEXPLAINED.
- A sixth run with the corrected tooling (`--timeout-seconds 120`) stored the
  last two hours and reported `ACQUISITION COMPLETE`: 244 of 244 items, 237
  populated and 7 scheduled closures, 4,629,911 raw bytes, within the
  20,000,000-byte ceiling.
- The first run stopped without a summary: `http.client.IncompleteRead`, raised
  when a connection drops mid-body, is not an `OSError` and escaped the
  transport. A later run stopped at the 400-request ceiling of that run.
- A `build` executed after the first, incomplete run registered six diagnostic
  datasets whose coverage states the gaps (EURUSD 10 of 120 hours, XAUUSD 0 of
  120). They are local, never committed, and never consumed.

Corrections made before closure, inside the D00 file scope:

1. every `http.client.HTTPException` is a retryable transport failure;
2. the journal records the last error of each failed item (`detail`);
3. `--timeout-seconds` (1 to 120) for slow provider responses;
4. an explicit completeness summary at the end of `acquire`;
5. `build` refuses pending items unless `--allow-incomplete` is given;
6. content-addressed canonical file and report names;
7. the instrument-aware, DST-aware calendar `ny-1700-close/1`, recorded in
   every tick and bar manifest.

None of these changes alters decoding, canonical serialization, aggregation,
cross-check policy, manifest schema, or any production contract.

## 19. Closure evidence

Validation of section 15, executed on 2026-11-24 from the corrected tooling of
commit `6d24500b4d596c365a687e01665718fdfc707f68` (Quality, CodeQL,
Documentation, and Research CI passed on that commit):

1. **Acquisition complete.** `ACQUISITION COMPLETE`, 244 of 244 planned items
   stored, 4,629,911 raw bytes.
2. **Build and registry.** `build` succeeded without warnings. Every dataset
   was re-verified independently of the D00 code: identity digest, canonical
   and compressed digests, row counts, lineage, and the raw digest and size of
   all 244 source files.
3. **Reproducibility.** A second `build` from copies of the raw files and the
   journal, in a fresh data root outside the repository, reproduced all eight
   `dataset_id` values.
4. **Cross-check reviewed** (policy `xcheck-h1/1`, tolerance 0 points):
   - EURUSD: `CONSISTENT`; all 234 derived H1 BID and ASK bars equal the
     provider candles exactly. This validates decoding, UTC alignment, and
     aggregation on real data.
   - XAUUSD: `DEVIATIONS_REPORTED`; 138 of 232 bars match, 94 bars carry 139
     field deviations (median 0.190, maximum 2.736 USD). Derived ranges are
     mostly wider (51 lower lows, 38 higher highs), and deviations cluster
     around the daily break at 21h–22h UTC. With identical code giving an exact
     match on EURUSD, the deviations reflect a difference between Dukascopy's
     XAUUSD tick and candle feeds, not a pipeline defect. In addition, the
     provider publishes a 14 March 21h UTC candle for an hour whose tick file
     is empty and which the calendar classifies as the scheduled daily break;
     it is reported as missing in derived. The owner accepted these documented
     provider differences. Ticks remain the authoritative source (A01 section
     10); the cross-check reports and never alters data.
5. **Dataset identities** (technical sample, partition `TECHNICAL`, never for
   strategy evaluation):

| Instrument | Dataset | Coverage | Rows | `dataset_id` |
| --- | --- | --- | --- | --- |
| EURUSD | ticks | 117 populated, 3 closures | 467,445 | `4f181694010c2f8ef9256d21ac68a94a78ad657b36b54e27cd285948f7206e8b` |
| EURUSD | H1 bars (from ticks) | 117 populated, 3 closures | 234 | `a4c33c19042a167c87928e934d46a6a90996616b25bd38567b38963428a05d31` |
| EURUSD | H4 bars (from ticks) | 117 populated, 3 closures | 60 | `2cbce30dc9a787937c67f88e64df6cf0ef8a2d002e2e0051c9eac5eb73cb17ec` |
| EURUSD | provider H1 candles | March 2012 | 1,052 | `a062854cd9ac0b2b70a70bb18e0c42e0918e5e884af3d0a716afbf3de2c45c32` |
| XAUUSD | ticks | 116 populated, 4 closures | 417,548 | `bdc05950f91477e55ec1dcff702a8e3325d5abdee1ae5452622e3de3089b45c6` |
| XAUUSD | H1 bars (from ticks) | 116 populated, 4 closures | 232 | `ce4d98346a842b077e7b11a0320c471ca7e7dad87e8653d0385976ea60adff5a` |
| XAUUSD | H4 bars (from ticks) | 116 populated, 4 closures | 60 | `ccda98c0c19e6ab6263c595a9072a3330ed1379db5e7af50a1e131f150994351` |
| XAUUSD | provider H1 candles | March 2012 | 1,052 | `30fa14bc4787bd32cbd973c81e5c37ffb239d5104366495780a166404669c36e` |

The six diagnostic datasets of the first, incomplete build remain in the local
registry, are superseded by these identities, and must never be consumed. No
dataset was consulted for research: the consultation ledger is unchanged.

Closing D00 authorizes nothing further. E00, Q00, and C00 remain not
authorized; P04-F02 remains not authorized pending research reconciliation;
P05 remains not authorized.
