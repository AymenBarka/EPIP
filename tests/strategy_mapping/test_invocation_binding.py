# mypy: disable-error-code="no-untyped-def,no-untyped-call"
import inspect

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *
from epip.strategy_runtime._base import digest
from epip.strategy_runtime.protocols import FactAdapterProtocol
from epip.strategy_runtime.provenance import FactAdapterIdentity


def _binding(semantic_profile):
    return AdapterInvocationBinding.create(
        adapter_identity=FactAdapterIdentity("adapter", "1", "p01-v1", "a" * 64),
        semantic_profile_identity=semantic_profile.identity,
        resolved_rule_set_id="b" * 64,
        typed_bundle_id="bundle",
        analytical_input_digest="c" * 64,
        provenance_manifest_id="manifest",
        instrument_binding_id="instrument",
    )


def test_binding_identity_and_roundtrip(semantic_profile):
    value = _binding(semantic_profile)
    assert value == from_json(AdapterInvocationBinding, to_json(value))
    assert digest(value, exclude=frozenset({"binding_id"})) == value.binding_id


def test_binding_tamper_fails(semantic_profile):
    value = _binding(semantic_profile)
    with pytest.raises(DataIntegrityError):
        AdapterInvocationBinding(
            value.schema_version,
            "0" * 64,
            value.adapter_identity,
            value.semantic_profile_identity,
            value.resolved_rule_set_id,
            value.typed_bundle_id,
            value.analytical_input_digest,
            value.provenance_manifest_id,
            value.instrument_binding_id,
        )


def test_p01_signature_continuity():
    assert tuple(inspect.signature(FactAdapterProtocol.adapt).parameters) == (
        "self",
        "context",
        "inputs",
        "profile",
        "policy",
    )
