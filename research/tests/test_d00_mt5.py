"""D00 acceptance 19-21: MT5 tick/bar imports and timezone handling."""

from __future__ import annotations

from datetime import UTC, datetime

import pytest

from research.datasets.contracts import DatasetIntegrityError, InstrumentSpec, PriceSide, Provider
from research.datasets.mt5 import (
    OffsetSegment,
    ServerTimeConvention,
    TimezoneUnresolvedError,
    canonical_bars_csv,
    canonical_ticks_csv,
    fixed_offset_convention,
    import_bars,
    import_ticks,
    segments_from,
)
from research.tests.fixtures import hour_ms

SPEC = InstrumentSpec("EURUSD", Provider.MT5, "EURUSD", 5)
BROKER = "AdmiralsGroup-Demo"
UTC2 = fixed_offset_convention(BROKER, 120, "owner-verified server clock")


def server(year: int, month: int, day: int, hour: int = 0, minute: int = 0) -> datetime:
    """Naive broker server time, as MT5 exports it."""
    return datetime(year, month, day, hour, minute, tzinfo=UTC).replace(tzinfo=None)


TICKS = (
    "<DATE>\t<TIME>\t<BID>\t<ASK>\t<LAST>\t<VOLUME>\t<FLAGS>\n"
    "2012.03.12\t02:00:00.125\t1.30000\t1.30003\t\t0\t6\n"
    "2012.03.12\t02:00:00.500\t1.30001\t\t\t0\t2\n"
    "2012.03.12\t02:00:01.000\t\t1.30005\t\t0\t4\n"
)
BARS = (
    "<DATE>\t<TIME>\t<OPEN>\t<HIGH>\t<LOW>\t<CLOSE>\t<TICKVOL>\t<VOL>\t<SPREAD>\n"
    "2012.03.12\t02:00:00\t1.30000\t1.30100\t1.29900\t1.30050\t812\t0\t12\n"
    "2012.03.12\t03:00:00\t1.30050\t1.3008\t1.3\t1.30060\t640\t0\t11\n"
)


def test_mt5_tick_import_converts_server_time_and_keeps_missing_sides() -> None:
    result = import_ticks(TICKS.encode(), BROKER, SPEC, UTC2)
    first, second, third = result.ticks
    assert first.timestamp_ms == hour_ms(2012, 3, 12, 0) + 125
    assert (first.bid_points, first.ask_points) == (130_000, 130_003)
    assert second.ask_points is None and second.bid_points == 130_001
    assert third.bid_points is None and third.ask_points == 130_005
    assert result.convention_source == "owner-verified server clock"
    csv = canonical_ticks_csv(result).decode()
    assert csv.splitlines()[2] == "2012-03-12T00:00:00.500Z,1.30001,,,0,2"


def test_mt5_tick_import_accepts_utf16_and_comma_exports() -> None:
    utf16 = import_ticks(TICKS.encode("utf-16"), BROKER, SPEC, UTC2)
    comma = import_ticks(TICKS.replace("\t", ",").encode("utf-8-sig"), BROKER, SPEC, UTC2)
    assert utf16.ticks == comma.ticks == import_ticks(TICKS.encode(), BROKER, SPEC, UTC2).ticks


def test_mt5_bar_import_requires_declared_side_and_keeps_spread() -> None:
    result = import_bars(BARS.encode(), BROKER, SPEC, PriceSide.BID, UTC2)
    assert [b.start_ms for b in result.bars] == [hour_ms(2012, 3, 12, 0), hour_ms(2012, 3, 12, 1)]
    assert result.bars[1].high_points == 130_080 and result.bars[1].low_points == 130_000
    assert [b.spread_points for b in result.bars] == [12, 11]
    assert all(b.side is PriceSide.BID for b in result.bars)
    assert canonical_bars_csv(result).decode().splitlines()[1].endswith(",812,0,12")
    with pytest.raises(DatasetIntegrityError, match="declared explicitly"):
        import_bars(BARS.encode(), BROKER, SPEC, None, UTC2)


def test_ambiguous_timezone_is_rejected_quarantine() -> None:
    with pytest.raises(TimezoneUnresolvedError, match="quarantined"):
        import_ticks(TICKS.encode(), BROKER, SPEC, None)
    with pytest.raises(TimezoneUnresolvedError):
        import_bars(BARS.encode(), BROKER, SPEC, PriceSide.BID, None)


def test_dst_overlap_is_ambiguous_and_gap_non_existent() -> None:
    # Server UTC+3 until 2012-10-28 01:00 UTC, then UTC+2 (fall back: local 03:00-04:00 twice).
    fall = ServerTimeConvention(
        BROKER,
        "table",
        segments_from(
            [
                (datetime(2012, 3, 25, 1, tzinfo=UTC), 180),
                (datetime(2012, 10, 28, 1, tzinfo=UTC), 120),
            ]
        ),
    )
    assert fall.to_utc_ms(server(2012, 10, 28, 2, 30)) == int(
        datetime(2012, 10, 27, 23, 30, tzinfo=UTC).timestamp() * 1000
    )
    with pytest.raises(TimezoneUnresolvedError, match="ambiguous"):
        fall.to_utc_ms(server(2012, 10, 28, 3, 30))
    assert fall.to_utc_ms(server(2012, 10, 28, 4, 30)) == int(
        datetime(2012, 10, 28, 2, 30, tzinfo=UTC).timestamp() * 1000
    )
    spring = ServerTimeConvention(
        BROKER,
        "table",
        segments_from(
            [(datetime(2011, 1, 1, tzinfo=UTC), 120), (datetime(2012, 3, 25, 1, tzinfo=UTC), 180)]
        ),
    )
    with pytest.raises(TimezoneUnresolvedError, match="non-existent"):
        spring.to_utc_ms(server(2012, 3, 25, 3, 30))
    with pytest.raises(TimezoneUnresolvedError, match="undefined"):
        spring.to_utc_ms(server(2010, 6, 1, 12, 0))


@pytest.mark.parametrize(
    ("text", "message"),
    [
        ("<DATE>\t<TIME>\t<BID>\n", "header"),
        ("", "empty"),
        (TICKS + "2012.03.12\t02:00:00.900\t1.30001\t1.30004\t\t0\n", "column count"),
        (TICKS + "2012.03.12\t01:59:59.000\t1.30001\t1.30004\t\t0\t6\n", "out of order"),
        (TICKS + TICKS.splitlines()[-1] + "\n", "duplicate"),
        (TICKS + "2012.03.12\t02:00:02.000\t1.30005\t1.30001\t\t0\t6\n", "ask below bid"),
        (TICKS + "2012.03.12\t02:00:02.000\t\t\t\t0\t6\n", "without BID/ASK"),
        (TICKS + "2012.03.12\t02:00:02.000\t1.300011\t\t\t0\t6\n", "more than 5 decimals"),
        (TICKS + "2012.13.12\t02:00:02.000\t1.30001\t\t\t0\t6\n", "timestamp"),
        (TICKS + "2012.03.12\t02:00:02.000\t0.00000\t\t\t0\t6\n", "positive"),
        (TICKS + "2012.03.12\t02:00:02.000\t1.30001\t\t\t-1\t6\n", "non-negative integer"),
    ],
)
def test_mt5_tick_anomalies_fail_closed(text: str, message: str) -> None:
    with pytest.raises(DatasetIntegrityError, match=message):
        import_ticks(text.encode(), BROKER, SPEC, UTC2)


def test_mt5_bar_anomalies_fail_closed() -> None:
    duplicate = BARS + BARS.splitlines()[-1] + "\n"
    with pytest.raises(DatasetIntegrityError, match="duplicated or out of order"):
        import_bars(duplicate.encode(), BROKER, SPEC, PriceSide.BID, UTC2)
    broken = BARS.replace("1.30100", "1.29000")
    with pytest.raises(DatasetIntegrityError, match="OHLC invalid"):
        import_bars(broken.encode(), BROKER, SPEC, PriceSide.BID, UTC2)


def test_broker_identity_and_encoding_checks() -> None:
    other = fixed_offset_convention("XMGlobal", 120, "x")
    with pytest.raises(DatasetIntegrityError, match="does not match"):
        import_ticks(TICKS.encode(), BROKER, SPEC, other)
    with pytest.raises(DatasetIntegrityError, match="broker"):
        import_ticks(TICKS.encode(), "", SPEC, UTC2)
    dukascopy_spec = InstrumentSpec("EURUSD", Provider.DUKASCOPY, "EURUSD", 5)
    with pytest.raises(DatasetIntegrityError, match="MT5 spec"):
        import_ticks(TICKS.encode(), BROKER, dukascopy_spec, UTC2)
    with pytest.raises(DatasetIntegrityError, match="encoding"):
        import_ticks(b"\xff\xfeA\xd8", BROKER, SPEC, UTC2)
    with pytest.raises(DatasetIntegrityError, match="not a bar import"):
        canonical_bars_csv(import_ticks(TICKS.encode(), BROKER, SPEC, UTC2))
    with pytest.raises(DatasetIntegrityError, match="not a tick import"):
        canonical_ticks_csv(import_bars(BARS.encode(), BROKER, SPEC, PriceSide.BID, UTC2))


def test_convention_validation() -> None:
    with pytest.raises(DatasetIntegrityError, match="UTC-aware"):
        OffsetSegment(server(2012, 1, 1), 0)
    with pytest.raises(DatasetIntegrityError, match="out of range"):
        OffsetSegment(datetime(2012, 1, 1, tzinfo=UTC), 15 * 60)
    seg = OffsetSegment(datetime(2012, 1, 1, tzinfo=UTC), 0)
    with pytest.raises(DatasetIntegrityError, match="unsorted"):
        ServerTimeConvention(BROKER, "s", (seg, seg))
    with pytest.raises(DatasetIntegrityError, match="at least one"):
        ServerTimeConvention(BROKER, "s", ())
    with pytest.raises(DatasetIntegrityError, match="naive"):
        UTC2.to_utc_ms(datetime(2012, 1, 1, tzinfo=UTC))
