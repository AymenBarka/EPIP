from dataclasses import FrozenInstanceError
from typing import Any, cast

import pytest

from epip.core.integrity import DataIntegrityError
from epip.governance import GovernanceEpoch
from epip.temporal.model import (
    CanonicalInstant,
    TemporalAuthorityReference,
    TemporalBoundary,
    TemporalDiagnosticCode,
    TemporalDiagnosticReason,
)
from epip.temporal.replay import (
    ReplayCompatibilityDiagnostics,
    ReplayCompatibilityValidation,
    ReplayCompatibilityValidator as _ReplayCompatibilityValidator,
)


def _context(boundary: TemporalBoundary) -> tuple[tuple[str, str], ...]:
    return (
        ("availability", str(boundary.availability.value)),
        ("calendar", boundary.calendar_identity or ""),
        ("closure", "closed" if boundary.validity is not None else "open"),
        ("mapping", boundary.timeframe_version or ""),
        ("revision", ",".join(boundary.revision_lineage)),
        ("timeframe", boundary.timeframe_identity or ""),
        ("watermark", str(boundary.knowledge.value)),
    )


class ReplayCompatibilityValidator:
    @classmethod
    def validate(cls, validation_identity: str, boundary: object, *args: Any, **kwargs: Any) -> Any:
        if not isinstance(boundary, TemporalBoundary):
            return _ReplayCompatibilityValidator.validate(
                validation_identity,
                cast(Any, boundary),
                *args,
                **kwargs,
            )
        assert isinstance(boundary, TemporalBoundary)
        kwargs.setdefault("predecessor_context", _context(boundary))
        return _ReplayCompatibilityValidator.validate(
            validation_identity, boundary, *args, **kwargs
        )


def _instant(value: int) -> CanonicalInstant:
    return CanonicalInstant(value, "second", "UTC", "UTC", "clock")


def _boundary() -> TemporalBoundary:
    return TemporalBoundary(
        "boundary",
        _instant(10),
        None,
        "validity-rule",
        _instant(1),
        _instant(2),
        _instant(20),
        None,
        _instant(100),
        None,
        _instant(10),
        _instant(15),
        "tf",
        "1",
        "cal",
        "1",
        ("artifact",),
        ("visible",),
        (("policy", "1"),),
        (TemporalAuthorityReference("authority", "temporal", "1", GovernanceEpoch(1)),),
    )


def test_replay_validation_is_deterministic_and_immutable() -> None:
    one = ReplayCompatibilityValidator.validate(
        "v", _boundary(), _instant(15), _instant(10), _instant(20)
    )
    two = ReplayCompatibilityValidator.validate(
        "v", _boundary(), _instant(15), _instant(10), _instant(20)
    )
    assert one == two
    assert hash(one) == hash(two)
    with pytest.raises(FrozenInstanceError):
        one.validations = ()


def test_future_replay_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="future knowledge"):
        ReplayCompatibilityValidator.validate(
            "v", _boundary(), _instant(21), _instant(10), _instant(20)
        )


def test_incompatible_basis_fails_closed() -> None:
    bad = CanonicalInstant(10, "second", "TAI", "UTC", "clock")
    with pytest.raises(DataIntegrityError, match="temporal basis"):
        ReplayCompatibilityValidator.validate("v", _boundary(), bad, _instant(10), _instant(20))


def test_invalid_inputs_and_diagnostic_paths_fail_closed() -> None:
    boundary = _boundary()
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidator.validate(
            "v", cast(Any, object()), _instant(15), _instant(10), _instant(20)
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidator.validate("v", boundary, object(), _instant(10), _instant(20))
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidator.validate("v", boundary, _instant(15), object(), _instant(20))
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidator.validate("v", boundary, _instant(15), _instant(10), object())
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidator.validate(
            "", boundary, _instant(15), _instant(10), _instant(20)
        )
    result = ReplayCompatibilityValidator.validate(
        "v", boundary, _instant(5), _instant(10), _instant(20)
    )
    assert result.reasons
    result = ReplayCompatibilityValidator.validate(
        "v", boundary, _instant(10), _instant(15), _instant(20)
    )
    assert result.reasons
    assert result != object()


def test_output_models_reject_invalid_and_duplicate_inputs() -> None:
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "", "b", _instant(1), _instant(1), _instant(2), True, True, "historical"
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v", "b", cast(Any, object()), _instant(1), _instant(2), True, True, "historical"
        )
    validation = ReplayCompatibilityValidator.validate(
        "v", _boundary(), _instant(15), _instant(10), _instant(20)
    ).validations[0]
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityDiagnostics([], ())  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityDiagnostics((validation, validation))
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v", "b", _instant(1), _instant(1), _instant(2), cast(Any, 1), True, "historical"
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v", "b", _instant(1), _instant(1), cast(Any, object()), True, True, "historical"
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v",
            "b",
            CanonicalInstant(1, "second", "TAI", "UTC", "clock"),
            _instant(1),
            _instant(2),
            True,
            True,
            "historical",
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityDiagnostics((validation,), (object(),))  # type: ignore[arg-type]


def test_context_modes_and_permutation_invariance_are_preserved() -> None:
    context = (
        ("availability", "2"),
        ("calendar", "cal"),
        ("closure", "open"),
        ("mapping", "1"),
        ("revision", "artifact"),
        ("timeframe", "tf"),
        ("watermark", "20"),
    )
    first = ReplayCompatibilityValidator.validate(
        "v",
        _boundary(),
        _instant(15),
        _instant(10),
        _instant(20),
        predecessor_context=context,
        historical_mode="operational_reproduction",
        revision_mode="revised_history",
    )
    second = ReplayCompatibilityValidator.validate(
        "v",
        _boundary(),
        _instant(15),
        _instant(10),
        _instant(20),
        predecessor_context=tuple(reversed(context)),
        historical_mode="operational_reproduction",
        revision_mode="revised_history",
    )
    assert first == second
    outcome = first.validations[0]
    assert outcome.predecessor_context == tuple(sorted(context))
    assert outcome.historical_mode == "operational_reproduction"
    assert outcome.revision_mode == "revised_history"
    assert hash(first) == hash(second)


def test_diagnostic_binding_rejects_orphans() -> None:
    validation = ReplayCompatibilityValidator.validate(
        "v", _boundary(), _instant(15), _instant(10), _instant(20)
    ).validations[0]
    reason = TemporalDiagnosticReason(
        TemporalDiagnosticCode.HISTORICAL_AMBIGUITY,
        "other",
        "b",
        "b",
        "tf",
        "cal",
        _instant(20),
        ("artifact",),
        "replay",
        "bad",
    )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityDiagnostics((validation,), (reason,))


def test_context_shape_and_uniqueness_fail_closed() -> None:
    base = {
        "validation_identity": "v",
        "boundary_identity": "b",
        "replay_time": _instant(1),
        "historical_time": _instant(1),
        "knowledge_boundary": _instant(2),
        "historical_visible": True,
        "exposure_valid": True,
        "mode": "historical",
    }
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(**base, predecessor_context=[])  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(**base, predecessor_context=(("bad",),))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(**base, predecessor_context=(("", "value"),))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(**base, predecessor_context=(("x", "y"), ("x", "y")))  # type: ignore[arg-type]


def test_context_mismatch_fails_closed() -> None:
    with pytest.raises(DataIntegrityError, match="context is inconsistent"):
        ReplayCompatibilityValidator.validate(
            "v",
            _boundary(),
            _instant(15),
            _instant(10),
            _instant(20),
            predecessor_context=(("availability", "wrong"),),
        )


def test_real_validator_context_failure_paths() -> None:
    boundary = _boundary()
    with pytest.raises(DataIntegrityError, match="missing or incomplete"):
        _ReplayCompatibilityValidator.validate(
            "v", boundary, _instant(15), _instant(10), _instant(20)
        )


def test_validation_model_remaining_fail_closed_paths() -> None:
    context = _context(_boundary())
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v",
            "boundary",
            _instant(1),
            _instant(1),
            _instant(2),
            cast(Any, 1),
            True,
            "historical",
            context,
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v",
            "boundary",
            cast(Any, object()),
            _instant(1),
            _instant(2),
            True,
            True,
            "historical",
            context,
        )
    with pytest.raises(DataIntegrityError):
        ReplayCompatibilityValidation(
            "v",
            "boundary",
            CanonicalInstant(1, "second", "TAI", "UTC", "clock"),
            _instant(1),
            _instant(2),
            True,
            True,
            "historical",
            context,
        )
