"""D00 acceptance 1-9: Dukascopy decoding (fail-closed)."""

from __future__ import annotations

import pytest

from research.datasets.contracts import (
    MS_PER_HOUR,
    DatasetIntegrityError,
    HourStatus,
    InstrumentSpec,
    PriceSide,
)
from research.datasets.dukascopy import (
    DUKASCOPY_INSTRUMENTS,
    SESSION_CALENDAR_VERSION,
    candle_relative_path,
    candle_url,
    classify_empty_hour,
    decode_candles,
    decode_ticks,
    instrument,
    new_york_offset_ms,
    tick_relative_path,
    tick_url,
    volume_micro,
)
from research.tests.fixtures import (
    candle_payload,
    encode,
    hour_ms,
    pack_tick,
    tick_payload,
    tick_records,
)

HOUR = hour_ms(2012, 3, 12, 10)


def test_valid_tick_decoding_maps_offsets_prices_and_volumes() -> None:
    records = tick_records("EURUSD", HOUR)
    ticks = decode_ticks(tick_payload(records), HOUR)
    assert len(ticks) == len(records)
    for tick, (offset, ask, bid, askv, bidv) in zip(ticks, records, strict=True):
        assert tick.timestamp_ms == HOUR + offset
        assert (tick.bid_points, tick.ask_points) == (bid, ask)
        assert tick.ask_volume_micro == round(askv * 1_000_000)
        assert tick.bid_volume_micro == round(bidv * 1_000_000)


@pytest.mark.parametrize("extra", [1, 7, 19])
def test_invalid_record_length_fails_closed(extra: int) -> None:
    raw = pack_tick(10, 130_002, 130_000, 1.0, 1.0) + b"\x00" * extra
    with pytest.raises(DatasetIntegrityError, match="multiple of 20"):
        decode_ticks(encode(raw), HOUR)


@pytest.mark.parametrize("payload", [b"not-lzma", b"\x5d\x00\x00\x80\x00" + b"\xff" * 20])
def test_invalid_lzma_payload_fails_closed(payload: bytes) -> None:
    with pytest.raises(DatasetIntegrityError, match="invalid LZMA"):
        decode_ticks(payload, HOUR)


def test_empty_payload_is_classified_not_decoded() -> None:
    with pytest.raises(DatasetIntegrityError, match="classified"):
        decode_ticks(b"", HOUR)
    with pytest.raises(DatasetIntegrityError, match="decompressed payload is empty"):
        decode_ticks(encode(b""), HOUR)


def test_instrument_specific_scaling_is_explicit() -> None:
    assert instrument("EURUSD").price_decimals == 5 and instrument("EURUSD").scale == 100_000
    assert instrument("XAUUSD").price_decimals == 3 and instrument("XAUUSD").scale == 1_000
    assert set(DUKASCOPY_INSTRUMENTS) == {"EURUSD", "XAUUSD"}
    with pytest.raises(DatasetIntegrityError, match="no configured Dukascopy scale"):
        instrument("GBPUSD")


@pytest.mark.parametrize("offset", [3_600_000, 3_600_001, 4_000_000_000])
def test_offsets_outside_the_utc_hour_fail(offset: int) -> None:
    with pytest.raises(DatasetIntegrityError, match="outside its UTC hour"):
        decode_ticks(encode(pack_tick(offset, 2, 1, 1.0, 1.0)), HOUR)


def test_hour_start_must_be_aligned() -> None:
    with pytest.raises(DatasetIntegrityError, match="not aligned"):
        decode_ticks(tick_payload(tick_records("EURUSD", HOUR)), HOUR + 1)


def test_last_millisecond_of_hour_is_inside() -> None:
    (tick,) = decode_ticks(encode(pack_tick(3_599_999, 2, 1, 0.0, 0.0)), HOUR)
    assert tick.timestamp_ms == HOUR + 3_599_999


def test_ask_below_bid_fails_closed() -> None:
    with pytest.raises(DatasetIntegrityError, match="ask below bid"):
        decode_ticks(encode(pack_tick(1, 100, 101, 1.0, 1.0)), HOUR)


def test_equal_bid_ask_is_accepted() -> None:
    (tick,) = decode_ticks(encode(pack_tick(1, 100, 100, 1.0, 1.0)), HOUR)
    assert tick.ask_points == tick.bid_points == 100


@pytest.mark.parametrize(
    ("ask", "bid", "askv", "bidv", "message"),
    [
        (0, 0, 1.0, 1.0, "non-positive price"),
        (5, 0, 1.0, 1.0, "non-positive price"),
        (5, 4, float("nan"), 1.0, "finite"),
        (5, 4, 1.0, float("inf"), "finite"),
        (5, 4, -1.0, 1.0, "non-negative"),
    ],
)
def test_invalid_prices_and_volumes_fail_closed(
    ask: int, bid: int, askv: float, bidv: float, message: str
) -> None:
    with pytest.raises(DatasetIntegrityError, match=message):
        decode_ticks(encode(pack_tick(1, ask, bid, askv, bidv)), HOUR)


def test_duplicate_tick_fails_closed() -> None:
    record = pack_tick(5, 130_002, 130_000, 1.0, 1.0)
    with pytest.raises(DatasetIntegrityError, match="duplicates"):
        decode_ticks(encode(record + record), HOUR)


def test_same_millisecond_distinct_quotes_are_kept_in_source_order() -> None:
    raw = pack_tick(5, 130_002, 130_000, 1.0, 1.0) + pack_tick(5, 130_003, 130_001, 1.0, 1.0)
    ticks = decode_ticks(encode(raw), HOUR)
    assert [t.bid_points for t in ticks] == [130_000, 130_001]


def test_out_of_order_ticks_fail_closed() -> None:
    raw = pack_tick(9, 130_002, 130_000, 1.0, 1.0) + pack_tick(8, 130_002, 130_000, 1.0, 1.0)
    with pytest.raises(DatasetIntegrityError, match="out of chronological order"):
        decode_ticks(encode(raw), HOUR)


def test_quoted_volume_is_quantized_to_millionths_half_even() -> None:
    assert volume_micro(0.75, "v") == 750_000
    assert volume_micro(1.12000000476837, "v") == 1_120_000
    assert volume_micro(0.0, "v") == 0


def test_candle_decoding_and_validation() -> None:
    rows = [(0, 100, 102, 99, 103, 5.0), (3600, 102, 101, 100, 104, 0.0)]
    candles = decode_candles(candle_payload(rows), 2012, 3, PriceSide.ASK)
    assert [c.start_ms for c in candles] == [hour_ms(2012, 3, 1, 0), hour_ms(2012, 3, 1, 1)]
    assert candles[0].open_points == 100 and candles[0].close_points == 102
    assert candles[0].low_points == 99 and candles[0].high_points == 103
    assert candles[1].volume_micro == 0 and candles[0].side is PriceSide.ASK


@pytest.mark.parametrize(
    ("rows", "message"),
    [
        ([(10, 1, 1, 1, 1, 1.0)], "hour boundary"),
        ([(3600, 1, 1, 1, 1, 1.0), (0, 1, 1, 1, 1, 1.0)], "out of order"),
        ([(0, 1, 1, 1, 1, 1.0), (0, 1, 1, 1, 1, 1.0)], "out of order"),
        ([(31 * 24 * 3600, 1, 1, 1, 1, 1.0)], "outside its month"),
        ([(0, 0, 1, 1, 1, 1.0)], "non-positive"),
        ([(0, 5, 5, 6, 7, 1.0)], "OHLC invalid"),
    ],
)
def test_candle_anomalies_fail_closed(
    rows: list[tuple[int, int, int, int, int, float]], message: str
) -> None:
    with pytest.raises(DatasetIntegrityError, match=message):
        decode_candles(candle_payload(rows), 2012, 3, PriceSide.BID)


def test_candle_record_length_and_side_type() -> None:
    with pytest.raises(DatasetIntegrityError, match="multiple of 24"):
        decode_candles(encode(b"\x00" * 25), 2012, 3, PriceSide.BID)
    with pytest.raises(DatasetIntegrityError, match="side invalid"):
        decode_candles(candle_payload([]), 2012, 3, "BID")  # type: ignore[arg-type]
    with pytest.raises(DatasetIntegrityError, match="classified"):
        decode_candles(b"", 2012, 3, PriceSide.BID)


def test_december_candles_roll_into_next_year() -> None:
    (candle,) = decode_candles(candle_payload([(0, 1, 1, 1, 1, 1.0)]), 2012, 12, PriceSide.BID)
    assert candle.start_ms == hour_ms(2012, 12, 1, 0)


def test_urls_use_zero_based_months_and_paths_one_based() -> None:
    spec = instrument("XAUUSD")
    assert tick_url(spec, HOUR).endswith("/XAUUSD/2012/02/12/10h_ticks.bi5")
    assert tick_relative_path(spec, HOUR) == "raw/dukascopy/XAUUSD/ticks/2012/03/12/10h_ticks.bi5"
    assert candle_url(spec, 2012, 3, PriceSide.ASK).endswith(
        "/XAUUSD/2012/02/ASK_candles_hour_1.bi5"
    )
    assert candle_relative_path(spec, 2012, 3, PriceSide.BID) == (
        "raw/dukascopy/XAUUSD/candles_h1/BID/2012-03.bi5"
    )


EURUSD = DUKASCOPY_INSTRUMENTS["EURUSD"]
XAUUSD = DUKASCOPY_INSTRUMENTS["XAUUSD"]
CLOSED = HourStatus.EXPECTED_CLOSURE
OPEN = HourStatus.EMPTY_UNEXPLAINED


@pytest.mark.parametrize(
    ("spec", "hour", "expected"),
    [
        # Summer time (EDT, UTC-4): Friday close 21h UTC, Sunday reopen 21h UTC.
        (EURUSD, (2012, 3, 16, 20), OPEN),
        (EURUSD, (2012, 3, 16, 21), CLOSED),
        (EURUSD, (2012, 3, 17, 10), CLOSED),
        (EURUSD, (2012, 3, 18, 20), CLOSED),
        (EURUSD, (2012, 3, 18, 21), OPEN),
        # Winter time (EST, UTC-5): Friday close 22h UTC, Sunday reopen 22h UTC.
        (EURUSD, (2012, 3, 2, 21), OPEN),
        (EURUSD, (2012, 3, 2, 22), CLOSED),
        (EURUSD, (2012, 3, 4, 21), CLOSED),
        (EURUSD, (2012, 3, 4, 22), OPEN),
        # DST starts on Sunday 2012-03-11 at 07:00 UTC: reopen at 21h UTC.
        (EURUSD, (2012, 3, 11, 20), CLOSED),
        (EURUSD, (2012, 3, 11, 21), OPEN),
        # Ordinary weekday hours are never a closure.
        (EURUSD, (2012, 3, 12, 10), OPEN),
        (EURUSD, (2012, 3, 14, 21), OPEN),
        # XAUUSD daily 17:00-18:00 New York break, Monday to Thursday only.
        (XAUUSD, (2012, 3, 14, 21), CLOSED),
        (XAUUSD, (2012, 3, 14, 22), OPEN),
        (XAUUSD, (2012, 3, 7, 22), CLOSED),
        (XAUUSD, (2012, 3, 7, 21), OPEN),
        (XAUUSD, (2012, 3, 18, 21), OPEN),
    ],
)
def test_empty_hour_calendar_is_instrument_and_dst_aware(
    spec: InstrumentSpec, hour: tuple[int, int, int, int], expected: HourStatus
) -> None:
    assert classify_empty_hour(spec, hour_ms(*hour)) is expected


def test_new_york_offset_follows_the_us_rule() -> None:
    start = hour_ms(2012, 3, 11, 7)
    end = hour_ms(2012, 11, 4, 6)
    assert new_york_offset_ms(start - 1) == -5 * MS_PER_HOUR
    assert new_york_offset_ms(start) == -4 * MS_PER_HOUR
    assert new_york_offset_ms(end - 1) == -4 * MS_PER_HOUR
    assert new_york_offset_ms(end) == -5 * MS_PER_HOUR
    with pytest.raises(DatasetIntegrityError, match="undefined for 2006"):
        classify_empty_hour(EURUSD, hour_ms(2006, 7, 1, 0))
    assert SESSION_CALENDAR_VERSION == "ny-1700-close/1"


def test_payload_type_is_checked() -> None:
    with pytest.raises(DatasetIntegrityError, match="must be bytes"):
        decode_ticks(bytearray(b"x"), HOUR)  # type: ignore[arg-type]
