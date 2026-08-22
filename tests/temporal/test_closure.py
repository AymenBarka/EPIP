from dataclasses import FrozenInstanceError

import pytest

from epip.core.integrity import DataIntegrityError, MissingFieldError
from epip.temporal.closure import (
    ClosureDiagnostics,
    IntegratedTemporalClosure,
    TemporalClosureVerifier,
)

FACTS = tuple((f"E0{i}", "verified") for i in range(10))


def test_terminal_closure_is_deterministic_and_immutable() -> None:
    one = TemporalClosureVerifier.verify("a05", FACTS)
    two = TemporalClosureVerifier.verify("a05", tuple(reversed(FACTS)))
    assert one == two
    assert hash(one) == hash(two)
    assert one.closures[0].complete is True
    with pytest.raises(FrozenInstanceError):
        one.closures = ()


def test_closure_rejects_missing_and_invalid_facts() -> None:
    with pytest.raises(MissingFieldError):
        TemporalClosureVerifier.verify("a05", FACTS[:-2])
    with pytest.raises(DataIntegrityError):
        TemporalClosureVerifier.verify("a05", [])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        TemporalClosureVerifier.verify("a05", FACTS + (("E00", "verified"),))
    with pytest.raises(MissingFieldError):
        IntegratedTemporalClosure("a05", (), True)
    with pytest.raises(DataIntegrityError):
        IntegratedTemporalClosure("a05", (("a",),), True)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        IntegratedTemporalClosure("a05", (("a", "1"), ("a", "1")), True)
    with pytest.raises(DataIntegrityError):
        IntegratedTemporalClosure("a05", (("a", "1"),), 1)  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        IntegratedTemporalClosure("a05", (("a", None),), True)
    with pytest.raises(DataIntegrityError):
        IntegratedTemporalClosure("a05", (("a", []),), True)


def test_diagnostics_reject_invalid_and_duplicate_entries() -> None:
    closure = IntegratedTemporalClosure("a05", FACTS, True)
    assert ClosureDiagnostics((closure,), ("incomplete",)).reasons == ("incomplete",)
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure, closure))
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure,), ("",))
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure,), (1,))  # type: ignore[arg-type]
    with pytest.raises(MissingFieldError):
        ClosureDiagnostics(())
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((1,))  # type: ignore[arg-type]
    assert closure != object()
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure,), attributions=[])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure,), attributions=(("x", closure),), context=[])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics(
            (closure,),
            attributions=(("x", closure), ("x", closure)),
            context=closure.predecessor_facts,
        )
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics(
            (closure,), attributions=(("x", IntegratedTemporalClosure("b", FACTS, True)),)
        )
    with pytest.raises(DataIntegrityError):
        ClosureDiagnostics((closure,), attributions=(("x", closure),), context=(("E00", "other"),))
