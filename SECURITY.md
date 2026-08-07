# Security Policy

## Supported versions

| Version | Supported |
|---|---|
| 1.4.x | Yes |
| 1.3.x | Security fixes until the next minor release |
| 1.2.x and earlier | No |

Pre-release versions receive fixes only when explicitly announced. See
[SUPPORTED_VERSIONS.md](SUPPORTED_VERSIONS.md) for the maintenance policy.

## Reporting a vulnerability

Do not open a public issue for a suspected vulnerability. Use GitHub private vulnerability
reporting for this repository when available. If private reporting is unavailable, contact the
maintainer through a private channel listed on the repository owner's GitHub profile and include
`EPIP SECURITY` in the subject.

Include the affected version, component, impact, reproduction steps, proof of concept when safe,
and any suggested mitigation. Do not include credentials, personal data, live broker secrets, or
third-party data you are not authorized to share.

## Disclosure process

1. Submit the report privately with reproduction and impact details.
2. The maintainer acknowledges receipt and assigns a confidential tracking state.
3. Maintainers reproduce the issue, determine affected supported versions, and assess severity.
4. A fix and regression test are prepared on a restricted branch when required.
5. The reporter is invited to validate the remediation when practical.
6. Maintainers publish patched versions, a security advisory, upgrade instructions, and coordinated
   credit after users have a reasonable opportunity to update.

Public disclosure before remediation should occur only by mutual agreement or when necessary to
protect users from an already public, actively exploited issue.

## Responsible disclosure

Allow maintainers reasonable time to validate and remediate the issue before disclosure. Avoid
accessing accounts or systems you do not own, modifying data, degrading services, social
engineering, and automated testing against third-party brokers or data providers without consent.

## Security response SLA

| Milestone | Target |
|---|---|
| Acknowledgement | 3 business days |
| Initial triage and severity | 7 business days |
| Status update or remediation plan | 14 business days |
| Critical remediation target | 30 calendar days |
| High-severity remediation target | 60 calendar days |
| Moderate/low remediation | Scheduled by risk and release impact |

These are response targets, not contractual guarantees. Coordinated disclosure timing will be
agreed with the reporter. Valid reports may be credited with permission.

## Scope

Security concerns include unsafe serialization, dependency or workflow compromise, credential
exposure, adapter boundary violations, unauthorized broker interaction, denial of service, and
integrity failures that could alter official Decision, Risk, or Execution outputs.
