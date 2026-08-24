from typing import get_type_hints

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import FactAdapterProtocol, FactAdapterResult, FactAdapterState


def test_fact_adapter_protocol_is_contract_only() -> None:
    assert "return" in get_type_hints(FactAdapterProtocol.adapt)
    assert tuple(item.value for item in FactAdapterState) == (
        "ACCEPTED",
        "REJECTED",
        "INVALID_INPUT",
        "FAILED",
    )


def test_nonaccepted_adapter_result_cannot_contain_bundle() -> None:
    with pytest.raises(DataIntegrityError):
        FactAdapterResult(FactAdapterState.REJECTED, object(), ())  # type: ignore[arg-type]
    assert FactAdapterResult(FactAdapterState.REJECTED, None, ()).bundle is None
