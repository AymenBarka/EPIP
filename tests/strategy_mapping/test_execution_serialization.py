# mypy: disable-error-code="no-untyped-def"
import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


def test_value_candidate_and_manifest_round_trip(rule):
    value = SemanticValue(SemanticValueKind.TEXT, text_value="UP")
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=value,
    )
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "impl",
    )
    for item in (value, candidate, ResolvedRuleManifest.create((declaration,))):
        assert from_json(type(item), to_json(item)) == item


def test_unknown_type_and_enum_fail():
    with pytest.raises(DataIntegrityError):
        from_dict(SemanticValue, {"$type": "builtins:dict", "fields": {}})
    payload = to_dict(SemanticValue(SemanticValueKind.TEXT, text_value="x"))
    payload["fields"]["kind"]["value"] = "UNKNOWN"
    with pytest.raises((DataIntegrityError, ValueError)):
        from_dict(SemanticValue, payload)


def test_historical_candidate_payload_defaults_role_without_identity_drift(rule):
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.TEXT, text_value="UP"),
    )
    historical = to_dict(candidate)
    del historical["fields"]["role"]
    reconstructed = from_dict(SemanticCandidate, historical)
    assert reconstructed == candidate
    assert hash(reconstructed) == hash(candidate)
    assert reconstructed.candidate_id == candidate.candidate_id
    assert reconstructed.role is SemanticCandidateRole.UNSPECIFIED
    assert "role" in to_dict(reconstructed)["fields"]


def test_unknown_candidate_role_fails_closed(rule):
    candidate = SemanticCandidate.create(
        source_binding_id="s",
        provenance_ref="p",
        instrument_binding_id="i",
        timeframe="H1",
        source_rule_identity=rule,
        value=SemanticValue(SemanticValueKind.TEXT, text_value="UP"),
    )
    payload = to_dict(candidate)
    payload["fields"]["role"]["value"] = "UNKNOWN"
    with pytest.raises((DataIntegrityError, ValueError)):
        from_dict(SemanticCandidate, payload)
