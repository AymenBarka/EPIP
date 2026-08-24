from dataclasses import FrozenInstanceError, replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import StrategyProfile


def test_profile_is_immutable_and_fingerprint_bound(profile: StrategyProfile) -> None:
    assert hash(profile)
    with pytest.raises(FrozenInstanceError):
        profile.mtf_requirement = "other"  # type: ignore[misc]
    with pytest.raises(DataIntegrityError):
        replace(profile, mapping_rules_reference="changed")


def test_profile_rejects_overlapping_required_optional(profile: StrategyProfile) -> None:
    with pytest.raises(DataIntegrityError):
        replace(profile, optional_source_domains=("context",))
