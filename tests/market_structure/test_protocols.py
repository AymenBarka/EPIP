from __future__ import annotations

from epip.market_structure.bos_detector import BOSDetector
from epip.market_structure.choch_detector import CHOCHDetector
from epip.market_structure.protocols import StructureDetectorProtocol
from epip.market_structure.range_detector import RangeDetector
from epip.market_structure.trend_detector import TrendDetector


def test_detectors_implement_structure_detector_protocol() -> None:
    assert isinstance(TrendDetector(), StructureDetectorProtocol)
    assert isinstance(BOSDetector(), StructureDetectorProtocol)
    assert isinstance(CHOCHDetector(), StructureDetectorProtocol)
    assert isinstance(RangeDetector(), StructureDetectorProtocol)
