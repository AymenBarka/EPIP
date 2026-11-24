# P04-R01-Q00-CI00 — Research CI Hardening for the Causal Elliott Package

Status: **IMPLEMENTED / REMOTE CERTIFICATION PENDING**

CI00 implements the Research CI amendment frozen in
[P04-R01-Q00-G00](P04_R01_Q00_G00_QUANTITATIVE_VALIDATION_PROTOCOL_RECONCILIATION.md)
section 16. It closes only after Research, Quality, CodeQL, and Documentation
pass on the implementation SHA and a documentation-only closure commit records
that evidence (owner-approved two-commit procedure).

## 1. Authority and scope

Authorized by the owner's P04-R01-Q00-CI00 implementation authorization,
amended by the owner's approval of two atomic commits for CI00 only. The
starting SHA is `2141c285e4bc31aa4f054742fcc7ee1ae4b3c57b`, with HEAD equal to
`origin/develop`, a clean tracked tree, and the 18 historical untracked
artifacts preserved.

| Commit | Files |
| --- | --- |
| 1 — implementation | `.github/workflows/research.yml`, this record, `docs/project/ROADMAP.md` |
| 2 — closure (documentation only) | this record, `docs/project/ROADMAP.md` |

No file under `epip/`, `research/`, `tests/`, other workflows,
`pyproject.toml`, `requirements.txt`, or `data/` changes. No dependency is
installed or added.

## 2. Workflow change

`.github/workflows/research.yml` changes exactly as frozen in Q00-G00
section 16 (SHA-256 after the change:
`2ec24199a2e1da4dc6869edac9dd51db77c64d52c5ec165a82f416b40730f2c9`):

```diff
       - name: Black
-        run: python -m black --check research/datasets research/tests
+        run: python -m black --check research/datasets research/elliott_causal research/tests

       - name: Ruff
-        run: python -m ruff check research/datasets research/tests
+        run: python -m ruff check research/datasets research/elliott_causal research/tests

       - name: MyPy
-        run: python -m mypy --explicit-package-bases research/datasets research/tests
+        run: >-
+          python -m mypy --explicit-package-bases
+          research/datasets research/elliott_causal research/tests

       - name: Research tests and coverage
         run: >-
           python -m pytest -p no:cacheprovider research/tests
-          --cov=research/datasets --cov-report=term-missing --cov-fail-under=95
+          --cov=research/datasets --cov=research/elliott_causal
+          --cov-report=term-missing
+
+      - name: Per-package coverage gates
+        run: |
+          python -m coverage report --include="*/research/datasets/*" --fail-under=95
+          python -m coverage report --include="*/research/elliott_causal/*" --fail-under=95
```

These parts are unchanged:

- triggers and permissions;
- Python 3.13 and `PYTHONHASHSEED=0`;
- the dependency installation;
- the determinism rerun;
- the production isolation guard on `epip/`.

The combined `--cov-fail-under=95` is replaced by two independent
per-package gates of at least 95 %. Each package must pass on its own, so no
gate is weakened.

## 3. Local evidence (owner's Windows machine, before commit 1)

These results are local. Remote evidence is recorded only in section 4.

| Tool | Version |
| --- | --- |
| Python | 3.13.1 |
| black | 26.5.1 |
| ruff | 0.17.6 |
| mypy | 2.3.1 |
| pytest | 9.1.1 |
| pytest-cov | 7.1.0 |
| coverage | 7.15.4 |

| Check (exact section 16 commands) | Result |
| --- | --- |
| Black on `research/datasets research/elliott_causal research/tests` | 36 files unchanged, exit 0 |
| Ruff on the same paths | all checks passed, exit 0 |
| Strict MyPy on the same paths | no issues in 36 source files, exit 0 |
| Research tests with both `--cov` targets | 251 passed, exit 0 |
| Gate `*/research/datasets/*` at 95 % or more | 100 % (1,428 statements, 0 missed), exit 0 |
| Gate `*/research/elliott_causal/*` at 95 % or more | 100 % (625 statements, 0 missed), exit 0 |
| Determinism rerun | 251 passed, exit 0 |

The coverage data file was written to a temporary folder outside the
repository. The wildcard-prefixed include patterns matched Windows backslash
paths.

Repository checks on the identical tree:

| Check | Result |
| --- | --- |
| Production pytest collection | 3127 (no predecessor node removed) |
| Research collection | 251 |
| Compliance inventory / digest | 612 / `92b40f1dfec340c886345710bf4a446b5a2dafa753b7129c12c7d3488c46f3f1` |
| Markdownlint, MkDocs strict, `git diff --check` | pass |

## 4. Remote certification

Pending. Commit 2 records:

- the implementation SHA;
- the four workflow run IDs and conclusions;
- the step-level evidence that Black, Ruff, and MyPy checked
  `research/elliott_causal`;
- both per-package coverage percentages reported by Research CI;
- the test counts and the determinism rerun.

## 5. Frozen-contract preservation

No production file, research module, research test, frozen identity,
fingerprint, or compliance contract changes. The ledger is unchanged (two
TECHNICAL records), and no market data is read or acquired.

## 6. Limitations

- Lint tools are not version-pinned in the `dev` extra. Research CI installs
  the latest releases, so a future release may report new findings. Such
  findings are fixed under their own authorization, never waived.
- Coverage is statement coverage; branch coverage is not gated.
- `research/harness` is not yet covered. Its inclusion belongs to the Q00-I00
  authorization (Q00-G00 section 16).
