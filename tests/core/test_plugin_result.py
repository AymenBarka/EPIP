from __future__ import annotations

from epip.core.plugin_result import PluginResult


def test_plugin_result_is_immutable() -> None:
    result = PluginResult(
        plugin="demo",
        execution_time=0.25,
        success=True,
        errors=(),
        warnings=("alpha",),
        generated_evidence=(),
        metadata={"source": "test"},
    )

    assert result.plugin == "demo"
    assert result.success is True
    assert result.warnings == ("alpha",)
    assert result.metadata["source"] == "test"
