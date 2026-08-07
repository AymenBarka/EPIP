"""EPIP-010 configuration."""

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class MarketContextConfig:
    engine_version: str = "EPIP-010"
