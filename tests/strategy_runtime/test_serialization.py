import json

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import EvaluationContext, from_json, to_json


def test_context_canonical_json_round_trip(context: EvaluationContext) -> None:
    payload = to_json(context)
    assert from_json(EvaluationContext, payload) == context
    assert payload == to_json(context)


def test_serialization_rejects_unknown_type_and_nan() -> None:
    with pytest.raises(DataIntegrityError):
        from_json(EvaluationContext, json.dumps({"$type": "builtins:dict", "fields": {}}))
    with pytest.raises(DataIntegrityError):
        from_json(EvaluationContext, "NaN")
