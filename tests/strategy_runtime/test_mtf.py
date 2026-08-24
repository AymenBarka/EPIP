from dataclasses import replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import MultiTimeframeInputSet, TimeframeInput, TimeframeRole


def test_mtf_is_canonical_and_has_one_primary(mtf: MultiTimeframeInputSet) -> None:
    assert hash(mtf)
    with pytest.raises(DataIntegrityError):
        MultiTimeframeInputSet.create("H4", mtf.alignment_timestamp, mtf.frames)


def test_open_or_future_frame_fails(mtf: MultiTimeframeInputSet) -> None:
    frame = mtf.frames[0]
    with pytest.raises(DataIntegrityError):
        replace(frame, closed=False)
    future = TimeframeInput(
        "H4",
        TimeframeRole.HIGHER,
        "2026-08-24T12:00:00Z",
        "2026-08-24T16:00:00Z",
        "2026-08-24T16:00:00Z",
        True,
        ("future",),
        ("future",),
    )
    with pytest.raises(DataIntegrityError):
        MultiTimeframeInputSet.create("H1", mtf.alignment_timestamp, (*mtf.frames, future))
