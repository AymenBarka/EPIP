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
