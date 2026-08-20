"""CI guard for universal immutable-model integrity adoption."""

from pathlib import Path

from epip.core.integrity_compliance import (
    compliance_digest,
    render_report,
    scan_immutable_dataclasses,
)

EXPECTED_DIGEST = "890777d70f31b01961b68032eeab45c614797eec500c468a0a6a542d3a82cdd6"


def test_every_immutable_business_dataclass_is_in_compliance_inventory() -> None:
    entries = scan_immutable_dataclasses(Path("epip"))
    assert entries
    assert all(entry.mode in {"explicit", "structural"} for entry in entries)
    assert compliance_digest(entries) == EXPECTED_DIGEST, (
        "Immutable business-model inventory changed. Review the new model's invariants, "
        "then update the approved compliance digest.\n" + render_report(entries)
    )


def test_automated_compliance_report_covers_every_inventory_entry() -> None:
    entries = scan_immutable_dataclasses(Path("epip"))
    report = render_report(entries)
    assert all(entry.qualified_name in report for entry in entries)
