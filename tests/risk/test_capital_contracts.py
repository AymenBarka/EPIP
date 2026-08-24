from dataclasses import fields

from epip.a07.signal import StrategySignal
from epip.risk import SizedPositionPlan
from epip.strategy_runtime import EvaluationContext, FactAdapterIdentity, StrategySignalEnvelope
from epip.strategy_runtime._base import digest


def test_sized_plan_nests_signal_geometry_without_copying_it(
    signal: StrategySignal,
    context: EvaluationContext,
    adapter_identity: FactAdapterIdentity,
) -> None:
    envelope = StrategySignalEnvelope.create(
        signal=signal,
        context=context,
        adapter_identity=adapter_identity,
        provenance_manifest_id="manifest",
        runtime_version="1",
    )
    values = {
        "signal_envelope": envelope,
        "quantity": 2.0,
        "notional": 200.0,
        "capital_at_risk": 10.0,
        "leverage": 1.0,
        "margin_required": 20.0,
        "constraint_evidence": ("within-limits",),
        "accepted_at_evaluation_id": context.evaluation_id,
    }
    plan = SizedPositionPlan(
        digest(values),
        envelope,
        2.0,
        200.0,
        10.0,
        1.0,
        20.0,
        ("within-limits",),
        context.evaluation_id,
    )
    names = {item.name for item in fields(plan)}
    assert (
        not {"direction", "entry", "stop", "target", "risk", "reward", "rr", "confidence"} & names
    )
    assert plan.signal_envelope.signal is signal
