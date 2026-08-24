"""Typed confidence-model policy contracts; no model execution."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping._base import boolean, exact, finite, text
from epip.strategy_mapping.direction_policy import NonAcceptanceAction, SourceSelector
from epip.strategy_mapping.rule_identity import RuleIdentity


class ConfidenceModelKind(Enum):
    DIRECT = "DIRECT"
    WEIGHTED = "WEIGHTED"
    RULE = "RULE"
    CALIBRATED = "CALIBRATED"


@dataclass(frozen=True, slots=True)
class ConfidenceInput:
    input_key: str
    source_selector: SourceSelector
    required: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "input_key", text(self.input_key, "input_key"))
        exact(self.source_selector, SourceSelector, "source_selector")
        boolean(self.required, "required")


@dataclass(frozen=True, slots=True, order=True)
class ModelParameter:
    parameter_key: str
    value: float

    def __post_init__(self) -> None:
        object.__setattr__(self, "parameter_key", text(self.parameter_key, "parameter_key"))
        object.__setattr__(self, "value", finite(self.value, "value"))


@dataclass(frozen=True, slots=True)
class ConfidencePolicy:
    policy_identity: RuleIdentity
    model_kind: ConfidenceModelKind
    model_identity: RuleIdentity
    inputs: tuple[ConfidenceInput, ...]
    parameters: tuple[ModelParameter, ...]
    calibration_identity: RuleIdentity | None
    output_min: float
    output_max: float
    missing_action: NonAcceptanceAction
    conflict_action: NonAcceptanceAction

    def __post_init__(self) -> None:
        exact(self.policy_identity, RuleIdentity, "policy_identity")
        exact(self.model_kind, ConfidenceModelKind, "model_kind")
        exact(self.model_identity, RuleIdentity, "model_identity")
        if (
            type(self.inputs) is not tuple
            or not self.inputs
            or any(type(item) is not ConfidenceInput for item in self.inputs)
        ):
            raise DataIntegrityError("inputs must be a non-empty ConfidenceInput tuple")
        inputs = tuple(sorted(self.inputs, key=lambda item: item.input_key))
        if len({item.input_key for item in inputs}) != len(inputs):
            raise DataIntegrityError("confidence input keys must be unique")
        object.__setattr__(self, "inputs", inputs)
        if type(self.parameters) is not tuple or any(
            type(item) is not ModelParameter for item in self.parameters
        ):
            raise DataIntegrityError("parameters must be a ModelParameter tuple")
        parameters = tuple(sorted(self.parameters))
        if len({item.parameter_key for item in parameters}) != len(parameters):
            raise DataIntegrityError("model parameter keys must be unique")
        object.__setattr__(self, "parameters", parameters)
        if self.model_kind is ConfidenceModelKind.DIRECT and len(inputs) != 1:
            raise DataIntegrityError("DIRECT confidence requires exactly one input")
        calibrated = self.model_kind is ConfidenceModelKind.CALIBRATED
        if calibrated != (self.calibration_identity is not None):
            raise DataIntegrityError("calibration identity is required only for CALIBRATED")
        if self.calibration_identity is not None:
            exact(self.calibration_identity, RuleIdentity, "calibration_identity")
        if (
            finite(self.output_min, "output_min") != 0.0
            or finite(self.output_max, "output_max") != 1.0
        ):
            raise DataIntegrityError("confidence output domain must be exactly [0, 1]")
        exact(self.missing_action, NonAcceptanceAction, "missing_action")
        exact(self.conflict_action, NonAcceptanceAction, "conflict_action")


__all__ = ["ConfidenceInput", "ConfidenceModelKind", "ConfidencePolicy", "ModelParameter"]
