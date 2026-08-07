# Supported Versions

## Current support matrix

| Release line | Status | Maintenance |
| --- | --- | --- |
| 1.4.x | Active | Security fixes, correctness fixes, documentation and compatible improvements |
| 1.3.x | Maintenance | Critical/high security fixes until 1.5.0 is released |
| 1.2.x and earlier | End of life | No planned fixes |
| Pre-releases | Evaluation | Best effort only; not production-supported |

## Maintenance policy

The latest minor release is actively supported. The immediately preceding minor release receives
critical and high-severity security fixes for one minor-release cycle. Support may be extended when
announced in release notes. Patches preserve public API compatibility unless a security issue makes
that impossible; any exception is documented prominently.

## End-of-life policy

A release reaches end of life when it falls outside the support window or is explicitly retired.
No fixes, compatibility updates, or vulnerability remediation are guaranteed after that date.
Users should upgrade through each release's migration and release notes and rerun their own quality,
replay, risk, and execution validation before production use.
