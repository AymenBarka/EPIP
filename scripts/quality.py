from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TARGETS = ["epip", "tests"]


def run_step(name: str, command: list[str]) -> int:
    print(f"\n[{name}]")
    print(" ".join(command))
    result = subprocess.run(command, cwd=ROOT, check=False)
    if result.returncode != 0:
        print(f"{name} failed with exit code {result.returncode}")
    return result.returncode


def main() -> int:
    steps = [
        ("Black", [sys.executable, "-m", "black", "--check", *TARGETS]),
        ("Ruff", [sys.executable, "-m", "ruff", "check", *TARGETS]),
        ("Mypy", [sys.executable, "-m", "mypy", *TARGETS]),
        ("Pytest", [sys.executable, "-m", "pytest", "--cov=epip", "--cov-report=term-missing"]),
    ]

    failures = []
    for name, command in steps:
        exit_code = run_step(name, command)
        if exit_code != 0:
            failures.append(name)

    if failures:
        print(f"\nQuality check failed: {', '.join(failures)}")
        return 1

    print("\nQuality check passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
