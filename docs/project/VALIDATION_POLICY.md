# Validation Policy

## Rules

- Validate at construction and at publication boundaries.
- Reject rather than clamp, coerce, ignore, or repair invalid input.
- Preserve documented numeric scales for each domain.
- Use explicit subclasses of `DataIntegrityError`.
- Keep error messages stable enough to identify the failed field.
- Preserve valid legacy serialization defaults.

## Numeric Domains

| Domain | Valid range |
| --- | --- |
| Probability, confidence, fraction | `0.0..1.0` |
| Signed institutional bias | `-1.0..1.0` |
| Percentage score | `0.0..100.0` |
| Quantity, commission, exposure | finite and non-negative |
| Tradable price | finite and positive |
| PnL and slippage | finite, signed values allowed |
| Version | positive integer, booleans rejected |

## Review Requirement

Every new public business object must document its invariants, implement construction-time checks,
and include valid, invalid, boundary, NaN, infinity and serialization tests where applicable.

Every public deserializer uses the shared integrity guard. Malformed payloads expose domain
exceptions, while valid legacy defaults remain readable.
