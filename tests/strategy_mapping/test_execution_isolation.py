# mypy: disable-error-code="no-untyped-def"
import ast
from pathlib import Path


def test_execution_contracts_have_no_forbidden_capabilities():
    root = Path("epip/strategy_mapping")
    files = (
        "rule_execution.py",
        "rule_values.py",
        "rule_requests.py",
        "rule_results.py",
        "resolved_rules.py",
        "invocation_binding.py",
        "evidence_identity.py",
    )
    forbidden_imports = {
        "pickle",
        "cloudpickle",
        "dill",
        "socket",
        "requests",
        "urllib",
        "importlib",
        "random",
    }
    forbidden_calls = {"eval", "exec", "open", "__import__"}
    for name in files:
        tree = ast.parse((root / name).read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                modules = (
                    [x.name for x in node.names]
                    if isinstance(node, ast.Import)
                    else [node.module or ""]
                )
                assert not any(x.split(".")[0] in forbidden_imports for x in modules)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
