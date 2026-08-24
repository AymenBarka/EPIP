import ast
from pathlib import Path


def test_contract_packages_have_no_forbidden_dependencies_or_ambient_state() -> None:
    roots = (
        *Path("epip/strategy_runtime").glob("*.py"),
        Path("epip/risk/capital_contracts.py"),
        Path("epip/risk/portfolio_risk_view.py"),
    )
    forbidden_imports = ("epip.execution", "epip.portfolio", "epip.execution.mt5_adapter")
    forbidden_calls = {"now", "utcnow", "time", "uuid4"}
    for path in roots:
        tree = ast.parse(path.read_text(encoding="utf-8"))
        imports = [node.module or "" for node in ast.walk(tree) if isinstance(node, ast.ImportFrom)]
        assert not any(item.startswith(forbidden_imports) for item in imports), path
        calls = {
            node.func.attr
            for node in ast.walk(tree)
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute)
        }
        assert not calls & forbidden_calls, path


def test_no_mode_specific_strategy_runtime_classes() -> None:
    names: set[str] = set()
    for path in Path("epip/strategy_runtime").glob("*.py"):
        tree = ast.parse(path.read_text(encoding="utf-8"))
        names.update(node.name for node in ast.walk(tree) if isinstance(node, ast.ClassDef))
    assert not {"BacktestStrategyRuntime", "PaperStrategyRuntime", "LiveStrategyRuntime"} & names
