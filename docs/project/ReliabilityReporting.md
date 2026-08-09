# Reliability Reporting

`ReliabilityReport` consolidates statistics, metrics, violations, diagnostics,
observations, snapshots, history, and failure classification. Reports are
immutable and comparable.

`to_json()` emits canonical JSON with sorted keys and compact separators.
Identical inputs therefore produce byte-identical reports. Report generation is
read-only and does not own recovery or control-plane decisions.
