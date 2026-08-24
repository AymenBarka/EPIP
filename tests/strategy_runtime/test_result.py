import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime import (
    DiagnosticSeverity,
    RuntimeDiagnostic,
    RuntimeDiagnosticCode,
    RuntimeDiagnosticStage,
    StrategyRuntimeDiagnostics,
    StrategyRuntimeResult,
    StrategyRuntimeState,
)
from epip.strategy_runtime._base import digest


def test_diagnostics_are_deduplicated_and_ordered() -> None:
    item = RuntimeDiagnostic(
        RuntimeDiagnosticCode.NO_SIGNAL,
        RuntimeDiagnosticStage.RESULT,
        DiagnosticSeverity.INFO,
        "request",
        (),
        "No signal",
    )
    diagnostics = StrategyRuntimeDiagnostics.create(
        StrategyRuntimeState.NO_SIGNAL, RuntimeDiagnosticStage.RESULT, (item, item)
    )
    assert diagnostics.entries == (item,)


def test_runtime_result_state_envelope_invariant() -> None:
    diagnostics = StrategyRuntimeDiagnostics.create(
        StrategyRuntimeState.NO_SIGNAL, RuntimeDiagnosticStage.RESULT, ()
    )
    values = {
        "contract_version": "p01-v1",
        "request_id": "request",
        "state": StrategyRuntimeState.NO_SIGNAL,
        "fact_bundle_id": None,
        "signal_envelope": None,
        "diagnostics": diagnostics,
        "runtime_version": "1",
    }
    result = StrategyRuntimeResult(
        "p01-v1",
        digest(values),
        "request",
        StrategyRuntimeState.NO_SIGNAL,
        None,
        None,
        diagnostics,
        "1",
    )
    assert result.state is StrategyRuntimeState.NO_SIGNAL
    with pytest.raises(DataIntegrityError):
        StrategyRuntimeResult(
            "p01-v1",
            "0" * 64,
            "request",
            StrategyRuntimeState.NO_SIGNAL,
            None,
            None,
            diagnostics,
            "1",
        )
