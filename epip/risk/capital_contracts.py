"""Additive Capital Risk successor contracts; no sizing engine behavior."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from epip.core.integrity import DataIntegrityError
from epip.risk.portfolio_risk_view import PortfolioRiskView
from epip.strategy_runtime._base import CONTRACT_VERSION, digest, finite, text
from epip.strategy_runtime.signal_envelope import StrategySignalEnvelope


class CapitalRiskState(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    INVALID_INPUT = "INVALID_INPUT"


@dataclass(frozen=True, slots=True)
class CapitalRiskReason:
    code: str
    message: str
    accepted: bool

    def __post_init__(self) -> None:
        object.__setattr__(self, "code", text(self.code, "code"))
        object.__setattr__(self, "message", text(self.message, "message"))
        if type(self.accepted) is not bool:
            raise DataIntegrityError("accepted must be bool")


@dataclass(frozen=True, slots=True)
class CapitalRiskRequest:
    contract_version: str
    request_id: str
    signal_envelope: StrategySignalEnvelope
    portfolio_risk_view: PortfolioRiskView
    capital_policy_identity: str
    capital_policy_version: str
    request_digest: str

    def __post_init__(self) -> None:
        if self.contract_version != CONTRACT_VERSION:
            raise DataIntegrityError("unsupported capital-risk contract version")
        for name in ("capital_policy_identity", "capital_policy_version"):
            object.__setattr__(self, name, text(getattr(self, name), name))
        expected = digest(self, exclude=frozenset({"request_id", "request_digest"}))
        if self.request_id != expected or self.request_digest != expected:
            raise DataIntegrityError("capital-risk request identity mismatch")


@dataclass(frozen=True, slots=True)
class SizedPositionPlan:
    plan_id: str
    signal_envelope: StrategySignalEnvelope
    quantity: float
    notional: float
    capital_at_risk: float
    leverage: float
    margin_required: float
    constraint_evidence: tuple[str, ...]
    accepted_at_evaluation_id: str

    def __post_init__(self) -> None:
        for name in ("quantity", "notional", "capital_at_risk", "leverage", "margin_required"):
            object.__setattr__(self, name, finite(getattr(self, name), name, non_negative=True))
        if self.quantity <= 0.0 or self.notional <= 0.0:
            raise DataIntegrityError(
                "accepted position plans require positive quantity and notional"
            )
        if type(self.constraint_evidence) is not tuple or not self.constraint_evidence:
            raise DataIntegrityError("constraint_evidence must be a non-empty tuple")
        object.__setattr__(
            self, "constraint_evidence", tuple(sorted(set(self.constraint_evidence)))
        )
        object.__setattr__(
            self,
            "accepted_at_evaluation_id",
            text(self.accepted_at_evaluation_id, "accepted_at_evaluation_id"),
        )
        if self.accepted_at_evaluation_id != self.signal_envelope.evaluation_id:
            raise DataIntegrityError("plan and signal evaluation identities differ")
        if self.plan_id != digest(self, exclude=frozenset({"plan_id"})):
            raise DataIntegrityError("plan_id does not match canonical sizing content")


@dataclass(frozen=True, slots=True)
class CapitalRiskAssessment:
    assessment_id: str
    request_id: str
    state: CapitalRiskState
    sized_plan: SizedPositionPlan | None
    reasons: tuple[CapitalRiskReason, ...]
    policy_reference: str

    def __post_init__(self) -> None:
        accepted = self.state is CapitalRiskState.ACCEPTED
        if accepted != (self.sized_plan is not None):
            raise DataIntegrityError("only accepted assessments contain a sized plan")
        if type(self.reasons) is not tuple or not self.reasons:
            raise DataIntegrityError("capital-risk reasons must be non-empty")
        object.__setattr__(self, "request_id", text(self.request_id, "request_id"))
        object.__setattr__(
            self, "policy_reference", text(self.policy_reference, "policy_reference")
        )
        if self.assessment_id != digest(self, exclude=frozenset({"assessment_id"})):
            raise DataIntegrityError("assessment_id does not match canonical content")
