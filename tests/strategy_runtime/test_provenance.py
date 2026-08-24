from dataclasses import replace

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import ProvenanceManifest


def test_manifest_is_canonical_hashable_and_complete(provenance: ProvenanceManifest) -> None:
    assert hash(provenance)
    assert tuple(item.fact_key for item in provenance.facts) == tuple(
        sorted(item.fact_key for item in provenance.facts)
    )


def test_dangling_fact_source_and_identity_mismatch_fail(provenance: ProvenanceManifest) -> None:
    bad_fact = replace(provenance.facts[0], source_refs=("missing",))
    with pytest.raises(DataIntegrityError):
        ProvenanceManifest.create(
            provenance.sources,
            (bad_fact, *provenance.facts[1:]),
            provenance.profile_identity,
            provenance.adapter_identity,
            provenance.evaluation_id,
        )
    with pytest.raises(DataIntegrityError):
        replace(provenance, manifest_id="0" * 64)
