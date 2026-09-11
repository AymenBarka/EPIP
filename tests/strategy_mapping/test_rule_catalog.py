# mypy: disable-error-code="no-untyped-call,no-untyped-def"
from dataclasses import FrozenInstanceError

import pytest

from epip.core.integrity import DataIntegrityError
from epip.strategy_mapping import *


def _entry(rule, state, implementation_id=None):
    return SemanticRuleCatalogEntry(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        state,
        implementation_id,
    )


def test_catalog_states_are_closed_and_entries_fail_closed(rule):
    assert {item.value for item in SemanticRuleCatalogState} == {
        "EXECUTABLE",
        "DECLARATION_ONLY",
    }
    executable = _entry(rule, SemanticRuleCatalogState.EXECUTABLE, "implementation-v1")
    declared = _entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY)
    assert executable.implementation_id == "implementation-v1"
    assert declared.implementation_id is None
    with pytest.raises(DataIntegrityError):
        _entry(rule, SemanticRuleCatalogState.EXECUTABLE)
    with pytest.raises(DataIntegrityError):
        _entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY, "placeholder")
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalogEntry(
            rule,
            SemanticRuleFamily.SOURCE_EXTRACTION,
            SemanticInvocationKind.SOURCE_EXTRACTION,
            SemanticResultKind.CANDIDATES,
            "EXECUTABLE",  # type: ignore[arg-type]
            "implementation-v1",
        )
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalogEntry(
            rule,
            SemanticRuleFamily.CONFIDENCE,
            SemanticInvocationKind.SOURCE_EXTRACTION,
            SemanticResultKind.CANDIDATES,
            SemanticRuleCatalogState.EXECUTABLE,
            "implementation-v1",
        )


def test_catalog_is_non_empty_unique_immutable_and_deterministic(rule):
    other = RuleIdentity("other", "1", FOUNDATION_SCHEMA_VERSION, "b" * 64)
    entries = (
        _entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY),
        _entry(other, SemanticRuleCatalogState.EXECUTABLE, "other-v1"),
    )
    first = SemanticRuleCatalog.create(entries)
    second = SemanticRuleCatalog.create(tuple(reversed(entries)))
    assert first == second
    assert hash(first) == hash(second)
    assert first.catalog_id == second.catalog_id
    assert tuple(item.identity.reference for item in first.entries) == tuple(
        sorted(item.identity.reference for item in entries)
    )
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog.create(())
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog.create((object(),))  # type: ignore[arg-type]
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog(EXECUTION_SCHEMA_VERSION, "0" * 64, ())
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog("unknown", "0" * 64, entries)
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog.create((entries[0], entries[0]))
    with pytest.raises(FrozenInstanceError):
        first.catalog_id = "changed"  # type: ignore[misc]


def test_catalog_identity_covers_state_and_implementation(rule):
    declared = SemanticRuleCatalog.create(
        (_entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY),)
    )
    executable = SemanticRuleCatalog.create(
        (_entry(rule, SemanticRuleCatalogState.EXECUTABLE, "implementation-v1"),)
    )
    changed = SemanticRuleCatalog.create(
        (_entry(rule, SemanticRuleCatalogState.EXECUTABLE, "implementation-v2"),)
    )
    assert len({declared.catalog_id, executable.catalog_id, changed.catalog_id}) == 3
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog(EXECUTION_SCHEMA_VERSION, "0" * 64, declared.entries)


def test_executable_manifest_excludes_declaration_only_entries(rule):
    other = RuleIdentity("other", "1", FOUNDATION_SCHEMA_VERSION, "b" * 64)
    catalog = SemanticRuleCatalog.create(
        (
            _entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY),
            _entry(other, SemanticRuleCatalogState.EXECUTABLE, "other-v1"),
        )
    )
    manifest = catalog.executable_manifest()
    assert tuple(item.identity for item in manifest.declarations) == (other,)
    assert manifest.declarations[0].implementation_id == "other-v1"
    with pytest.raises(DataIntegrityError):
        SemanticRuleCatalog.create(
            (_entry(rule, SemanticRuleCatalogState.DECLARATION_ONLY),)
        ).executable_manifest()


def test_catalog_round_trip(rule):
    catalog = SemanticRuleCatalog.create(
        (_entry(rule, SemanticRuleCatalogState.EXECUTABLE, "implementation-v1"),)
    )
    assert from_json(SemanticRuleCatalog, to_json(catalog)) == catalog


def test_historical_manifest_identity_fixture_is_unchanged(rule):
    declaration = SemanticRuleDeclaration(
        rule,
        SemanticRuleFamily.SOURCE_EXTRACTION,
        SemanticInvocationKind.SOURCE_EXTRACTION,
        SemanticResultKind.CANDIDATES,
        "synthetic-v1",
    )
    assert ResolvedRuleManifest.create((declaration,)).rule_set_id == (
        "2f75aac4cc625863edb2efade7b0190a35e7ad38c01ce41272699eb24e285d86"
    )
