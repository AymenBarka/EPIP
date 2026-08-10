# Security Reporting

`SecurityReport` is an immutable projection containing a summary, normalized
snapshot, metrics, violations, diagnostics, compliance status, and audit history.

`to_dict()` produces primitive values. `to_json()` sorts keys and uses compact
separators, providing byte-identical JSON for identical inputs. Reports are
descriptive and must not be interpreted as authorization decisions.
