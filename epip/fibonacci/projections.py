"""Immutable profit targets and dynamic projection service."""

from dataclasses import dataclass
from enum import StrEnum


class ProjectionLabel(StrEnum):
    TP1 = "TP1"
    TP2 = "TP2"
    TP3 = "TP3"
    DYNAMIC = "DYNAMIC"


@dataclass(frozen=True, slots=True)
class ProjectionTarget:
    label: ProjectionLabel
    ratio: float
    price: float
    probability: float = 0.0
    confluence_score: float = 0.0


def project_targets(
    start: float,
    end: float,
    probability: float,
    ratios: tuple[float, ...] = (1.272, 1.618, 2.618),
) -> tuple[ProjectionTarget, ...]:
    distance = end - start
    labels = (ProjectionLabel.TP1, ProjectionLabel.TP2, ProjectionLabel.TP3)
    bounded_probability = max(0.0, min(1.0, probability))
    return tuple(
        ProjectionTarget(
            label,
            ratio,
            start + distance * ratio,
            bounded_probability,
            max(0.0, bounded_probability - index * 0.1),
        )
        for index, (label, ratio) in enumerate(zip(labels, ratios, strict=True))
    )


def dynamic_projection(
    start: float, end: float, ratio: float, probability: float
) -> ProjectionTarget:
    bounded_probability = max(0.0, min(1.0, probability))
    return ProjectionTarget(
        ProjectionLabel.DYNAMIC,
        ratio,
        start + (end - start) * ratio,
        bounded_probability,
        bounded_probability,
    )
