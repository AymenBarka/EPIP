# Security Audit Architecture

## Purpose

The security-audit layer provides deterministic evidence about H007 declarations
and caller-supplied runtime observations. It is an observability boundary, not an
enforcement boundary.

## Components

- `SecurityAuditRegistry` stores immutable audit references.
- `SecurityAuditManager` creates snapshots, diagnostics, and reports.
- `SecuritySnapshot` captures entries, observations, statistics, and coverage.
- `SecurityDiagnostics` describes objective declaration inconsistencies.
- `SecurityReport` combines summary, compliance, metrics, violations, and history.
- `SecurityAuditAware` permits explicit additive adoption by applications.

## Dependency direction

The module reads only the official H007 registries: security contracts, security
boundaries, input-validation contracts, runtime-security policies, and
secure-failure contracts. Those registries do not depend on the audit layer.

## Invariants

- all report models are frozen;
- ordering uses stable names, logical time, and observation identity;
- JSON output is canonical;
- no implicit clock, identity, network, filesystem, or runtime calls occur;
- audit results cannot change the object being observed.
