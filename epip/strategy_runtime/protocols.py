"""P01 protocol-only Fact Adapter boundary."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Protocol

from epip.a07.policy import StrategyPolicy
from epip.core.integrity import DataIntegrityError
from epip.strategy_runtime.context import EvaluationContext
from epip.strategy_runtime.facts import AnalyticalInputBundle, StrategyFactBundle
from epip.strategy_runtime.profile import StrategyProfile
from epip.strategy_runtime.provenance import FactAdapterIdentity
from epip.strategy_runtime.result import RuntimeDiagnostic


class FactAdapterState(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INVALID_INPUT = "INVALID_INPUT"
    FAILED = "FAILED"


@dataclass(frozen=True, slots=True)
class FactAdapterResult:
    state: FactAdapterState
    bundle: StrategyFactBundle | None
    diagnostics: tuple[RuntimeDiagnostic, ...]

    def __post_init__(self) -> None:
        accepted = self.state is FactAdapterState.ACCEPTED
        if accepted != (self.bundle is not None):
            raise DataIntegrityError("only ACCEPTED adapter results contain a bundle")
        if type(self.diagnostics) is not tuple:
            raise DataIntegrityError("adapter diagnostics must be a tuple")


class FactAdapterProtocol(Protocol):
    @property
    def identity(self) -> FactAdapterIdentity: ...

    def adapt(
        self,
        context: EvaluationContext,
        inputs: AnalyticalInputBundle,
        profile: StrategyProfile,
        policy: StrategyPolicy,
    ) -> FactAdapterResult: ...
