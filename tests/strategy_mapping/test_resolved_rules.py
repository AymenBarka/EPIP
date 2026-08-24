# mypy: disable-error-code="no-untyped-def,no-untyped-call"
from dataclasses import dataclass

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


@dataclass(frozen=True)
class SyntheticRule:
    identity: RuleIdentity
    family: SemanticRuleFamily
    invocation_kind: SemanticInvocationKind
    result_kind: SemanticResultKind
    implementation_id: str

    def invoke(self, request: SemanticRuleRequest) -> SemanticRuleResult:
        return CandidateRuleResult(
            SemanticRuleState.NO_MATCH, (SemanticRuleDiagnosticCode.SELECTOR_NO_MATCH,), None
        )


def _resolved(rule):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "synthetic-v1",
    )
    manifest = ResolvedRuleManifest.create((declaration,))
    implementation = SyntheticRule(
        rule,
        declaration.family,
        declaration.invocation_kind,
        declaration.result_kind,
        declaration.implementation_id,
    )
    return ResolvedSemanticRuleSet(manifest, (implementation,))


def test_manifest_and_rule_set_identity_are_deterministic(rule):
    first = _resolved(rule)
    second = _resolved(rule)
    assert first == second and hash(first) == hash(second)
    assert first.resolve(rule).identity == rule


def test_manifest_tamper_and_duplicate_fail(rule):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "x",
    )
    with pytest.raises(DataIntegrityError):
        ResolvedRuleManifest(EXECUTION_SCHEMA_VERSION, "0" * 64, (declaration,))
    with pytest.raises(DataIntegrityError):
        ResolvedRuleManifest.create((declaration, declaration))


def test_family_kind_mismatch_fails(rule):
    with pytest.raises(DataIntegrityError):
        SemanticRuleDeclaration(
            rule,
            SemanticRuleFamily.CONFIDENCE,
            SemanticInvocationKind.DIRECTION,
            SemanticResultKind.DIRECTION,
            "x",
        )


def test_runtime_declaration_mismatch_fails(rule):
    resolved = _resolved(rule)
    implementation = resolved.implementations[0]
    bad = SyntheticRule(
        rule,
        SemanticRuleFamily.CONFIDENCE,
        implementation.invocation_kind,
        implementation.result_kind,
        implementation.implementation_id,
    )
    with pytest.raises(DataIntegrityError):
        ResolvedSemanticRuleSet(resolved.manifest, (bad,))


def test_exact_profile_closure_rejects_incompatible_foundation_fixture(rule, semantic_profile):
    with pytest.raises(DataIntegrityError):
        _resolved(rule).validate_profile_closure(semantic_profile)
