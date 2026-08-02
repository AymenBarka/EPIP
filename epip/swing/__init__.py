"""Swing Engine exports for EPIP-006."""

from epip.swing.config import SwingConfig
from epip.swing.detector import SwingDetector
from epip.swing.engine import SwingEngine
from epip.swing.events import (
    SwingConfirmed,
    SwingDetected,
    SwingMerged,
    SwingRejected,
    SwingUpdated,
)
from epip.swing.filters import (
    ATRFilter,
    CompositeSwingFilter,
    DistanceFilter,
    DuplicateFilter,
    MinimumMoveFilter,
    NoiseFilter,
    TrendFilter,
    build_default_filters,
)
from epip.swing.metrics import SwingMetrics
from epip.swing.models import Swing, SwingPoint, SwingSequence
from epip.swing.pivot_detector import (
    ATRAdaptiveStrategy,
    FractalStrategy,
    HybridStrategy,
    ZigZagStrategy,
)
from epip.swing.pivot_window_detector import PivotWindowStrategy
from epip.swing.statistics import SwingStatistics, SwingStatisticsCollector
from epip.swing.types import PivotType, SwingClassification, SwingScope, TrendBias
from epip.swing.validators import PivotValidator, PriceValidator, SequenceValidator

__all__ = [
    "ATRAdaptiveStrategy",
    "ATRFilter",
    "CompositeSwingFilter",
    "DistanceFilter",
    "DuplicateFilter",
    "FractalStrategy",
    "HybridStrategy",
    "MinimumMoveFilter",
    "NoiseFilter",
    "PivotType",
    "PivotValidator",
    "PivotWindowStrategy",
    "PriceValidator",
    "SequenceValidator",
    "Swing",
    "SwingClassification",
    "SwingConfig",
    "SwingConfirmed",
    "SwingDetected",
    "SwingDetector",
    "SwingEngine",
    "SwingMerged",
    "SwingMetrics",
    "SwingPoint",
    "SwingRejected",
    "SwingScope",
    "SwingSequence",
    "SwingStatistics",
    "SwingStatisticsCollector",
    "SwingUpdated",
    "TrendBias",
    "TrendFilter",
    "ZigZagStrategy",
    "build_default_filters",
]
