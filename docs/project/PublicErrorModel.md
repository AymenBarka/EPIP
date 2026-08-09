# Public Error Model

Public APIs should expose stable EPIP concepts rather than provider, adapter,
operating-system, or implementation-specific exceptions.

The Public API Boundary declares that framework and infrastructure failures may
be translated or wrapped as `EPIPError`. Programme B does not perform that
translation. Existing public behaviour remains authoritative until runtime
adoption is separately approved.

Public errors must remain:

- attributable to one responsibility;
- classified by one failure category;
- stable across implementation changes;
- free from secret or provider-specific diagnostic content;
- explicit about whether caller correction is expected.
