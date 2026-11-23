"""P04-R01-D00 research dataset foundation (research-only, never imported by ``epip``)."""

from research.datasets.contracts import (
    MANIFEST_SCHEMA_VERSION,
    TICK_NORMALIZATION_VERSION,
    DatasetIntegrityError,
)

__all__ = ["MANIFEST_SCHEMA_VERSION", "TICK_NORMALIZATION_VERSION", "DatasetIntegrityError"]
