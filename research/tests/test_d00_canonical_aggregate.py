"""D00 acceptance 10-18: canonical bytes, hashing, gzip, H1/H4 bars, cross-check."""

from __future__ import annotations

import gzip
import random

import pytest

from research.datasets.aggregate import aggregate, interval_start
from research.datasets.canonical import (
    bars_to_csv,
    csv_to_bars,
    csv_to_ticks,
    deterministic_gzip,
    format_points,
    format_timestamp,
    gunzip,
    parse_points,
    parse_timestamp,
    sha256_hex,
    ticks_to_csv,
)
from research.datasets.contracts import (
    MS_PER_HOUR,
    Bar,
    BarCoverage,
    DatasetIntegrityError,
    Granularity,
    HourStatus,
    PriceSide,
    Tick,
)
from research.datasets.crosscheck import CROSSCHECK_POLICY_VERSION, crosscheck_h1
from research.datasets.dukascopy import ProviderCandle, decode_ticks, instrument
from research.tests.fixtures import hour_ms, tick_payload, tick_records

EUR = instrument("EURUSD")
XAU = instrument("XAUUSD")
H0 = hour_ms(2012, 3, 12, 0)


def _ticks(hours: int, symbol: str = "EURUSD") -> tuple[Tick, ...]:
    out: list[Tick] = []
    for h in range(hours):
        start = H0 + h * MS_PER_HOUR
        out.extend(decode_ticks(tick_payload(tick_records(symbol, start)), start))
    return tuple(out)


def _status(hours: int, status: HourStatus = HourStatus.POPULATED) -> dict[int, HourStatus]:
    return {H0 + h * MS_PER_HOUR: status for h in range(hours)}


def test_canonical_tick_csv_is_frozen_and_round_trips() -> None:
    tick = Tick(H0 + 1_234, 130_000, 130_003, 750_000, 1_500_000)
    data = ticks_to_csv((tick,), EUR)
    assert data == (
        b"timestamp_utc,bid,ask,bid_volume,ask_volume\n"
        b"2012-03-12T00:00:01.234Z,1.30000,1.30003,0.750000,1.500000\n"
    )
    assert csv_to_ticks(data, EUR) == (tick,)


def test_xauusd_prices_render_with_three_decimals() -> None:
    data = ticks_to_csv((Tick(H0, 1_700_123, 1_700_456, 0, 0),), XAU)
    assert b"1700.123,1700.456" in data


def test_serialization_is_deterministic_and_checksums_stable() -> None:
    ticks = _ticks(6)
    first, second = ticks_to_csv(ticks, EUR), ticks_to_csv(ticks, EUR)
    assert first == second and sha256_hex(first) == sha256_hex(second)
    payload = tick_payload(tick_records("EURUSD", H0))
    assert sha256_hex(payload) == sha256_hex(bytes(payload))


def test_property_seeded_random_ticks_round_trip() -> None:
    rng = random.Random(20120312)
    for _ in range(25):
        t = H0
        ticks = []
        for _ in range(rng.randint(1, 40)):
            t += rng.randint(0, 5000)
            bid = rng.randint(1, 10**8)
            ticks.append(
                Tick(
                    t, bid, bid + rng.randint(0, 900), rng.randint(0, 10**9), rng.randint(0, 10**9)
                )
            )
        data = ticks_to_csv(ticks, EUR)
        assert csv_to_ticks(data, EUR) == tuple(ticks)
        assert gunzip(deterministic_gzip(data)) == data


def test_gzip_is_deterministic_with_zero_mtime_and_no_name() -> None:
    data = ticks_to_csv(_ticks(3), EUR)
    a, b = deterministic_gzip(data), deterministic_gzip(data)
    assert a == b
    assert a[4:8] == b"\x00\x00\x00\x00"
    assert a[3] & 0x08 == 0
    assert gzip.decompress(a) == data
    assert sha256_hex(gunzip(a)) == sha256_hex(data)


@pytest.mark.parametrize(
    "bad",
    [
        b"wrong,header\n",
        b"timestamp_utc,bid,ask,bid_volume,ask_volume\r\n",
        b"timestamp_utc,bid,ask,bid_volume,ask_volume\n2012-03-12T00:00:00.000Z,1.3,1.30003,0.1,0.1\n",
        b"timestamp_utc,bid,ask,bid_volume,ask_volume\n2012-03-12T00:00:00.000Z,1.30000\n",
        b"timestamp_utc,bid,ask,bid_volume,ask_volume\n2012-03-12 00:00:00.000Z,1.30000,1.30003,0.100000,0.100000\n",
    ],
)
def test_canonical_parser_rejects_noncanonical_input(bad: bytes) -> None:
    with pytest.raises(DatasetIntegrityError):
        csv_to_ticks(bad, EUR)


def test_timestamp_and_decimal_helpers() -> None:
    assert parse_timestamp(format_timestamp(H0 + 999)) == H0 + 999
    assert format_points(5, 3) == "0.005" and parse_points("0.005", 3) == 5
    for bad in ("2012-03-12T00:00:00.00xZ", "2012-03-12T00:00:00Z"):
        with pytest.raises(DatasetIntegrityError):
            parse_timestamp(bad)
    with pytest.raises(DatasetIntegrityError):
        format_points(-1, 2)
    with pytest.raises(DatasetIntegrityError):
        format_timestamp(-1)


def test_h1_aggregation_per_side_with_tick_counts() -> None:
    ticks = _ticks(3)
    bars = aggregate(ticks, PriceSide.BID, Granularity.H1, _status(3))
    assert [b.start_ms for b in bars] == [H0 + h * MS_PER_HOUR for h in range(3)]
    for bar in bars:
        hour = [t for t in ticks if bar.start_ms <= t.timestamp_ms < bar.end_ms]
        bids = [t.bid_points for t in hour]
        assert (bar.open_points, bar.close_points) == (bids[0], bids[-1])
        assert (bar.high_points, bar.low_points) == (max(bids), min(bids))
        assert bar.tick_count == len(hour) and bar.coverage is BarCoverage.COMPLETE
    asks = aggregate(ticks, PriceSide.ASK, Granularity.H1, _status(3))
    assert all(a.high_points >= b.high_points for a, b in zip(asks, bars, strict=True))


def test_h4_aggregation_spans_four_hours() -> None:
    ticks = _ticks(8)
    bars = aggregate(ticks, PriceSide.ASK, Granularity.H4, _status(8))
    assert [(b.start_ms, b.end_ms) for b in bars] == [
        (H0, H0 + 4 * MS_PER_HOUR),
        (H0 + 4 * MS_PER_HOUR, H0 + 8 * MS_PER_HOUR),
    ]
    assert sum(b.tick_count for b in bars) == len(ticks)
    assert interval_start(H0 + 5 * MS_PER_HOUR + 1, Granularity.H4) == H0 + 4 * MS_PER_HOUR


def test_tick_on_boundary_belongs_to_next_interval() -> None:
    ticks = (Tick(H0 + MS_PER_HOUR - 1, 100, 101, 0, 0), Tick(H0 + MS_PER_HOUR, 200, 201, 0, 0))
    bars = aggregate(ticks, PriceSide.BID, Granularity.H1, _status(2))
    assert [(b.start_ms, b.tick_count, b.open_points) for b in bars] == [
        (H0, 1, 100),
        (H0 + MS_PER_HOUR, 1, 200),
    ]


def test_empty_interval_produces_no_bar() -> None:
    ticks = (Tick(H0, 100, 101, 0, 0), Tick(H0 + 2 * MS_PER_HOUR, 100, 101, 0, 0))
    status = _status(3)
    status[H0 + MS_PER_HOUR] = HourStatus.EMPTY_UNEXPLAINED
    bars = aggregate(ticks, PriceSide.BID, Granularity.H1, status)
    assert [b.start_ms for b in bars] == [H0, H0 + 2 * MS_PER_HOUR]


def test_incomplete_coverage_is_flagged_not_hidden() -> None:
    ticks = _ticks(2)
    status = _status(4)
    status[H0 + 2 * MS_PER_HOUR] = HourStatus.MISSING
    status[H0 + 3 * MS_PER_HOUR] = HourStatus.EXPECTED_CLOSURE
    (bar,) = aggregate(ticks, PriceSide.BID, Granularity.H4, status)
    assert bar.coverage is BarCoverage.INCOMPLETE
    status[H0 + 2 * MS_PER_HOUR] = HourStatus.EXPECTED_CLOSURE
    (bar,) = aggregate(ticks, PriceSide.BID, Granularity.H4, status)
    assert bar.coverage is BarCoverage.COMPLETE


def test_aggregation_guards() -> None:
    ticks = _ticks(1)
    with pytest.raises(DatasetIntegrityError, match="not classified POPULATED"):
        aggregate(ticks, PriceSide.BID, Granularity.H1, {})
    with pytest.raises(DatasetIntegrityError, match="chronological"):
        aggregate(tuple(reversed(ticks)), PriceSide.BID, Granularity.H1, _status(1))
    with pytest.raises(DatasetIntegrityError, match="H1 or H4"):
        aggregate(ticks, PriceSide.BID, Granularity.TICK, _status(1))


def test_bar_csv_round_trip_and_ordering() -> None:
    bars = aggregate(_ticks(2), PriceSide.ASK, Granularity.H1, _status(2)) + aggregate(
        _ticks(2), PriceSide.BID, Granularity.H1, _status(2)
    )
    data = bars_to_csv(bars, EUR)
    parsed = csv_to_bars(data, EUR)
    assert [(b.start_ms, b.side) for b in parsed] == sorted(
        [(b.start_ms, b.side) for b in bars], key=lambda k: (k[0], k[1].value)
    )
    assert set(parsed) == set(bars)
    with pytest.raises(DatasetIntegrityError):
        csv_to_bars(b"bad\n", EUR)


def _candle(bar: Bar, **change: int) -> ProviderCandle:
    values = {
        "open_points": bar.open_points,
        "high_points": bar.high_points,
        "low_points": bar.low_points,
        "close_points": bar.close_points,
        "volume_micro": 1,
    }
    values.update(change)
    return ProviderCandle(bar.start_ms, bar.side, **values)


def test_crosscheck_consistent_when_provider_matches() -> None:
    bars = aggregate(_ticks(3), PriceSide.BID, Granularity.H1, _status(3))
    report = crosscheck_h1(bars, [_candle(b) for b in bars], H0, H0 + 3 * MS_PER_HOUR)
    assert report.status == "CONSISTENT" and report.matched == report.compared == 3
    assert report.policy_version == CROSSCHECK_POLICY_VERSION and report.tolerance_points == 0


def test_crosscheck_reports_without_altering_values() -> None:
    bars = aggregate(_ticks(4), PriceSide.BID, Granularity.H1, _status(4))
    original = tuple(bars)
    candles = [
        _candle(bars[0], high_points=bars[0].high_points + 2),
        _candle(bars[1], volume_micro=0),
        _candle(bars[2]),
        ProviderCandle(H0 + 9 * MS_PER_HOUR, PriceSide.BID, 1, 1, 1, 1, 5),
        ProviderCandle(H0 + 99 * MS_PER_HOUR, PriceSide.BID, 1, 1, 1, 1, 5),
    ]
    report = crosscheck_h1(bars, candles, H0, H0 + 10 * MS_PER_HOUR)
    assert bars == original
    assert report.status == "DEVIATIONS_REPORTED"
    assert [(d.field, d.derived_points, d.provider_points) for d in report.deviations] == [
        ("high", bars[0].high_points, bars[0].high_points + 2)
    ]
    assert report.provider_filler == ((bars[1].start_ms, PriceSide.BID),)
    assert report.missing_in_provider == (
        (bars[1].start_ms, PriceSide.BID),
        (bars[3].start_ms, PriceSide.BID),
    )
    assert report.missing_in_derived == ((H0 + 9 * MS_PER_HOUR, PriceSide.BID),)


def test_crosscheck_flags_incomplete_and_rejects_bad_input() -> None:
    ticks = _ticks(1)
    status = _status(1)
    bars = aggregate(ticks, PriceSide.ASK, Granularity.H1, status)
    incomplete = (
        Bar(
            **{
                **{f: getattr(bars[0], f) for f in bars[0].__slots__},
                "coverage": BarCoverage.INCOMPLETE,
            }
        ),
    )
    report = crosscheck_h1(incomplete, [_candle(incomplete[0])], H0, H0 + MS_PER_HOUR)
    assert report.incomplete_derived == ((H0, PriceSide.ASK),)
    with pytest.raises(DatasetIntegrityError, match="window invalid"):
        crosscheck_h1(bars, [], H0, H0)
    with pytest.raises(DatasetIntegrityError, match="duplicate provider candle"):
        crosscheck_h1(bars, [_candle(bars[0]), _candle(bars[0])], H0, H0 + MS_PER_HOUR)
    h4 = aggregate(_ticks(4), PriceSide.ASK, Granularity.H4, _status(4))
    with pytest.raises(DatasetIntegrityError, match="expects H1"):
        crosscheck_h1(h4, [], H0, H0 + MS_PER_HOUR)
