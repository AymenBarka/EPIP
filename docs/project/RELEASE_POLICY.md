# Release Policy

## Version numbering

EPIP follows Semantic Versioning: `MAJOR.MINOR.PATCH`, optionally with a pre-release suffix. Major
versions may contain governed breaking changes; minor versions add backward-compatible capability;
patch versions contain compatible fixes and documentation. Tags use the annotated `vX.Y.Z` form.

## Branches and commits

Feature work starts from current `develop` on `feature/<scope>`, fixes on `fix/<scope>`, and
documentation on `docs/<scope>`. Commits use Conventional Commits. Release branches must contain no
unrelated changes, caches, environments, coverage files, generated reports, or user IDE settings.

## Review and merge

The feature branch is pushed for review. Public API or architecture changes require Chief Architect
approval. Approved changes merge into `develop` using `git merge --no-ff`; EPIP does not squash
away the reviewed feature lineage. A release manager resolves conflicts without opportunistic
refactoring.

## Quality gates

Before feature delivery and after merge, run `python scripts/quality.py`. Black, Ruff, strict MyPy,
and Pytest must pass and aggregate coverage must be at least 95%. Relevant benchmarks and
documentation workflows must pass. Any failure aborts the release.

## Tags and release notes

Create an annotated tag only after a green post-merge build and successful `develop` publication.
The annotation names the release and included framework modules. Every tag requires
`docs/project/releases/<tag>.md` with highlights, modules, architecture changes, tests, coverage,
quality, and benchmark context. Push tags individually and verify them on origin.

## Release evidence

Record the merge hash, branch status, quality results, test count, coverage, benchmark summary, tag
object hash, tag target, `develop` push result, and tag push result. Update `CHANGELOG.md`, roadmap,
support matrix, catalogs, and compatibility notes when applicable.

## Maintenance and security

Supported versions follow `SUPPORTED_VERSIONS.md`. Security releases follow `SECURITY.md`, may
override normal disclosure timing, and still require the maximum safe automated validation.
