# Resource Ownership Transfers

## Roles

| Role | Close | Transfer | Meaning |
| --- | --- | --- | --- |
| Owner | Yes | Yes | Direct lifecycle authority |
| Borrower | No | No | Temporary non-owning access |
| Shared Owner | Yes | Yes | Explicit shared authority |
| Transferred Owner | Yes | Yes | Authority received by transfer |
| External Owner | Yes | No | Lifecycle originates externally |

## Transfer policy

Transfers are explicit through `transfer_ownership(new_owner_id)`. The target
identifier must be non-empty. A borrower, external owner, closing resource, or
closed resource cannot initiate a transfer.

The handle records the new identifier and changes its role to Transferred
Owner. Resource identity and the wrapped object remain unchanged.

## Audit

Rejected close and transfer operations increment the ownership-violation
counter. The manager exposes non-zero counters in deterministic name order.
