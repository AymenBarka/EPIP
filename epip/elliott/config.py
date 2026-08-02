"""EPIP-011 configuration."""

from dataclasses import dataclass

from epip.elliott.models import WaveDegree


@dataclass(frozen=True, slots=True)
class ElliottConfig:
    default_degree: WaveDegree = WaveDegree.MINOR
    allow_diagonal_overlap: bool = True
    engine_version: str = "EPIP-011"
