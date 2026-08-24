# mypy: disable-error-code="no-untyped-def"
import pytest

from epip.a07.foundation import StrategyIdentity
from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import derive_evidence_set_identity
from epip.strategy_runtime.provenance import FactAdapterIdentity


def test_complete_evidence_identity_is_permutation_invariant(semantic_profile):
    args = {
        "strategy_identity": StrategyIdentity("s", "1"),
        "semantic_profile_identity": semantic_profile.identity,
        "adapter_identity": FactAdapterIdentity("a", "1", "p01-v1", "a" * 64),
        "typed_bundle_id": "bundle",
        "provenance_manifest_id": "manifest",
    }
    one = derive_evidence_set_identity(
        **args, entries=(("b", ("s2",), ("p2",)), ("a", ("s1",), ("p1",)))
    )
    two = derive_evidence_set_identity(
        **args, entries=(("a", ("s1",), ("p1",)), ("b", ("s2",), ("p2",)))
    )
    assert one == two and one.provenance == "manifest" and len(one.evidence_id) == 64


def test_evidence_identity_rejects_duplicate_keys(semantic_profile):
    with pytest.raises(DataIntegrityError):
        derive_evidence_set_identity(
            strategy_identity=StrategyIdentity("s", "1"),
            semantic_profile_identity=semantic_profile.identity,
            adapter_identity=FactAdapterIdentity("a", "1", "p01-v1", "a" * 64),
            typed_bundle_id="b",
            provenance_manifest_id="p",
            entries=(("x", ("s",), ("p",)), ("x", ("s2",), ("p2",))),
        )
