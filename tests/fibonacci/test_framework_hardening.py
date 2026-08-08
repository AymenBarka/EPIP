import pytest

from epip.core.event_bus import EventBus
from epip.fibonacci import (
    FibonacciCluster,
    FibonacciConfig,
    FibonacciDirection,
    FibonacciEngine,
    FibonacciQuality,
    FibonacciStrength,
    InstitutionalEntryZone,
    MultiTimeFrameAlignment,
    ProjectionLabel,
    ProjectionTarget,
    dynamic_projection,
    project_targets,
)
from epip.fibonacci.alignment import compute_alignment
from epip.fibonacci.models import (
    DiscountZone,
    FibonacciSnapshot,
    GoldenZone,
    OTEZone,
    PremiumZone,
)
from epip.fibonacci.serialization import object_from_json, object_to_json
from epip.fibonacci.statistics import FibonacciStatistics
from tests.fibonacci.helpers import inputs


def _snapshot(timeframe: str = "M15") -> FibonacciSnapshot:
    swings, structure, liquidity = inputs(timeframe=timeframe)
    return FibonacciEngine(config=FibonacciConfig(), event_bus=EventBus()).process(
        swings, structure, liquidity
    )


def test_strength_is_deterministic_bounded_and_classified() -> None:
    strength = FibonacciStrength.calculate(4, 3, 1.5)
    assert strength == FibonacciStrength.calculate(4, 3, 1.5)
    assert strength.quality is FibonacciQuality.VERY_HIGH
    assert 0.0 <= strength.confidence <= 1.0
    assert 0.0 <= strength.probability <= 1.0
    assert FibonacciStrength.calculate(-1, -2, -1).quality is FibonacciQuality.VERY_LOW


def test_cluster_and_institutional_zone_group_domain_evidence() -> None:
    snapshot = _snapshot()
    premium, discount, ote, golden = snapshot.zones
    cluster = FibonacciCluster(
        "cluster-1",
        snapshot.retracement,
        snapshot.extension,
        (
            OTEZone(**ote.__dict__)
            if hasattr(ote, "__dict__")
            else OTEZone(ote.low, ote.high, ote.name)
        ),
        GoldenZone(golden.low, golden.high, golden.name),
        PremiumZone(premium.low, premium.high, premium.name),
        DiscountZone(discount.low, discount.high, discount.name),
        0.8,
        0.75,
    )
    zone = InstitutionalEntryZone(
        snapshot.symbol,
        snapshot.timeframe,
        ote.low,
        golden.high,
        FibonacciDirection.BULLISH,
        cluster.ote,
        cluster.golden_zone,
        0.8,
        0.7,
        0.75,
        0.7,
    )
    assert cluster.ote.name == "OTE"
    assert zone.low <= zone.high
    assert object_from_json(FibonacciCluster, object_to_json(cluster)) == cluster
    assert object_from_json(InstitutionalEntryZone, object_to_json(zone)) == zone


def test_projection_targets_and_dynamic_projection() -> None:
    targets = project_targets(100.0, 110.0, 1.5)
    assert tuple(target.label for target in targets) == (
        ProjectionLabel.TP1,
        ProjectionLabel.TP2,
        ProjectionLabel.TP3,
    )
    assert all(0.0 <= target.probability <= 1.0 for target in targets)
    dynamic = dynamic_projection(100.0, 110.0, 2.0, -1.0)
    assert dynamic == ProjectionTarget(ProjectionLabel.DYNAMIC, 2.0, 120.0, 0.0, 0.0)
    assert object_from_json(ProjectionTarget, object_to_json(dynamic)) == dynamic


def test_multi_timeframe_alignment_and_serialization() -> None:
    snapshots = tuple(_snapshot(timeframe) for timeframe in ("M15", "H1", "H4", "D1"))
    alignment = compute_alignment(snapshots)
    assert alignment.alignment_score == 1.0
    assert object_from_json(MultiTimeFrameAlignment, object_to_json(alignment)) == alignment
    assert compute_alignment((_snapshot("M5"),)).alignment_score == 0.0


def test_snapshot_exposes_bounded_probability_and_strength_serializes() -> None:
    snapshot = _snapshot()
    assert 0.0 <= snapshot.probability <= 1.0
    payload = snapshot.to_dict()
    payload["probability"] = 2.0
    with pytest.raises(ValueError, match="probability"):
        snapshot.from_dict(payload)
    strength = FibonacciStrength.calculate(2, 1, 0.6)
    assert object_from_json(FibonacciStrength, object_to_json(strength)) == strength


def test_metrics_expose_hardening_dimensions() -> None:
    statistics = FibonacciStatistics()
    statistics.record(0.1, 0.8, 0.7)
    statistics.record_projection(True)
    statistics.record_projection(False)
    statistics.record_alignment(1.5)
    statistics.record_cluster()
    metrics = statistics.snapshot()
    assert metrics.projection_accuracy == 0.5
    assert metrics.average_probability == 0.7
    assert metrics.average_alignment == 1.0
    assert metrics.cluster_usage == 1


def test_invalid_projection_cardinality_is_explicit() -> None:
    with pytest.raises(ValueError):
        project_targets(100.0, 110.0, 0.5, (1.272, 1.618))
