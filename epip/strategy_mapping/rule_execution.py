"""Closed semantic-rule execution vocabulary and protocol."""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING, Protocol

from epip.strategy_mapping.rule_identity import RuleIdentity

EXECUTION_SCHEMA_VERSION = "p02-f02-v1"


class SemanticRuleFamily(Enum):
    SOURCE_EXTRACTION = "SOURCE_EXTRACTION"
    DIRECTION_MAPPING = "DIRECTION_MAPPING"
    CANDIDATE_SELECTION = "CANDIDATE_SELECTION"
    CANDIDATE_RANKING = "CANDIDATE_RANKING"
    BOUNDARY_SELECTION = "BOUNDARY_SELECTION"
    APPLICABILITY = "APPLICABILITY"
    PRECEDENCE = "PRECEDENCE"
    PRICE_TRANSFORMATION = "PRICE_TRANSFORMATION"
    CONFIDENCE = "CONFIDENCE"
    TEMPORAL_ELIGIBILITY = "TEMPORAL_ELIGIBILITY"
    EVIDENCE_MAPPING = "EVIDENCE_MAPPING"
    EVIDENCE_ORDERING = "EVIDENCE_ORDERING"
    MTF_AGGREGATION = "MTF_AGGREGATION"


class SemanticInvocationKind(Enum):
    SOURCE_EXTRACTION = "SOURCE_EXTRACTION"
    DIRECTION = "DIRECTION"
    SELECTION = "SELECTION"
    RANKING = "RANKING"
    BOUNDARY = "BOUNDARY"
    APPLICABILITY = "APPLICABILITY"
    PRICE_TRANSFORMATION = "PRICE_TRANSFORMATION"
    CONFIDENCE = "CONFIDENCE"
    TEMPORAL_ELIGIBILITY = "TEMPORAL_ELIGIBILITY"
    EVIDENCE_MAPPING = "EVIDENCE_MAPPING"
    EVIDENCE_ORDERING = "EVIDENCE_ORDERING"
    MTF_AGGREGATION = "MTF_AGGREGATION"


class SemanticResultKind(Enum):
    CANDIDATES = "CANDIDATES"
    DIRECTION = "DIRECTION"
    SELECTION = "SELECTION"
    RANKING = "RANKING"
    BOUNDARY = "BOUNDARY"
    APPLICABILITY = "APPLICABILITY"
    PRICE_TRANSFORMATION = "PRICE_TRANSFORMATION"
    CONFIDENCE = "CONFIDENCE"
    TEMPORAL_ELIGIBILITY = "TEMPORAL_ELIGIBILITY"
    EVIDENCE_MAPPING = "EVIDENCE_MAPPING"
    EVIDENCE_ORDERING = "EVIDENCE_ORDERING"
    MTF_AGGREGATION = "MTF_AGGREGATION"


class SemanticRuleState(Enum):
    SUCCESS = "SUCCESS"
    NO_MATCH = "NO_MATCH"
    REJECTED = "REJECTED"
    INVALID_INPUT = "INVALID_INPUT"
    FAILED = "FAILED"


class SemanticValueKind(Enum):
    TEXT = "TEXT"
    BOOLEAN = "BOOLEAN"
    FINITE_FLOAT = "FINITE_FLOAT"
    PRICE = "PRICE"
    PRICE_RANGE = "PRICE_RANGE"


class SemanticRuleDiagnosticCode(Enum):
    RULE_NOT_RESOLVED = "RULE_NOT_RESOLVED"
    RULE_IDENTITY_MISMATCH = "RULE_IDENTITY_MISMATCH"
    RULE_INPUT_INVALID = "RULE_INPUT_INVALID"
    RULE_OUTPUT_INVALID = "RULE_OUTPUT_INVALID"
    RULE_REJECTED = "RULE_REJECTED"
    SELECTOR_NO_MATCH = "SELECTOR_NO_MATCH"
    AMBIGUOUS_CANDIDATE = "AMBIGUOUS_CANDIDATE"
    EVIDENCE_IDENTITY_ERROR = "EVIDENCE_IDENTITY_ERROR"
    INVOCATION_BINDING_MISMATCH = "INVOCATION_BINDING_MISMATCH"


class ExecutableSemanticRule(Protocol):
    @property
    def identity(self) -> RuleIdentity: ...

    @property
    def family(self) -> SemanticRuleFamily: ...

    @property
    def invocation_kind(self) -> SemanticInvocationKind: ...

    @property
    def result_kind(self) -> SemanticResultKind: ...

    @property
    def implementation_id(self) -> str: ...

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult: ...


if TYPE_CHECKING:
    from epip.strategy_mapping.rule_requests import SemanticRuleRequest
    from epip.strategy_mapping.rule_results import SemanticRuleResult

__all__ = [
    "EXECUTION_SCHEMA_VERSION",
    "ExecutableSemanticRule",
    "SemanticInvocationKind",
    "SemanticResultKind",
    "SemanticRuleDiagnosticCode",
    "SemanticRuleFamily",
    "SemanticRuleState",
    "SemanticValueKind",
]
