"""Static compliance inventory for immutable EPIP business dataclasses."""

from __future__ import annotations

import ast
import hashlib
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True, slots=True)
class ComplianceEntry:
    """One immutable dataclass and its integrity adoption mode."""

    module: str
    name: str
    mode: str

    @property
    def qualified_name(self) -> str:
        return f"{self.module}.{self.name}"


def _dataclass_call(node: ast.expr) -> ast.Call | None:
    if isinstance(node, ast.Call) and getattr(node.func, "id", None) == "dataclass":
        return node
    return None


def scan_immutable_dataclasses(root: Path) -> tuple[ComplianceEntry, ...]:
    """Inventory every frozen dataclass without importing application modules."""
    entries: list[ComplianceEntry] = []
    for path in sorted(root.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = ".".join(path.with_suffix("").parts)
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            call = next(
                (value for item in node.decorator_list if (value := _dataclass_call(item))),
                None,
            )
            if call is None:
                continue
            frozen = any(
                keyword.arg == "frozen"
                and isinstance(keyword.value, ast.Constant)
                and keyword.value.value is True
                for keyword in call.keywords
            )
            if not frozen:
                continue
            methods = {
                item.name
                for item in node.body
                if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef))
            }
            mode = (
                "explicit"
                if methods.intersection({"__post_init__", "validate_integrity"})
                else "structural"
            )
            entries.append(ComplianceEntry(module, node.name, mode))
    return tuple(sorted(entries, key=lambda item: item.qualified_name))


def compliance_digest(entries: tuple[ComplianceEntry, ...]) -> str:
    """Return a stable fingerprint used by the CI adoption guard."""
    payload = "\n".join(f"{entry.qualified_name}:{entry.mode}" for entry in entries).encode()
    return hashlib.sha256(payload).hexdigest()


def render_report(entries: tuple[ComplianceEntry, ...]) -> str:
    """Render the automated adoption report as Markdown."""
    lines = ["| Business dataclass | Contract |", "| --- | --- |"]
    lines.extend(f"| `{item.qualified_name}` | {item.mode} |" for item in entries)
    return "\n".join(lines)
