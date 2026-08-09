# Pipeline Execution Model

## Ordered Phases

1. `BEGIN PIPELINE`
2. `VALIDATION`
3. `BUILD CONTEXT`
4. `EXECUTE PLUGIN`
5. `VALIDATE RESULT`
6. `STORE TEMP RESULT`
7. repeat from `BUILD CONTEXT`
8. `COMMIT PIPELINE`
9. `EVENTS`
10. `RETURN`

The ordered plugin tuple is captured at validation. Every successful result and event remains
private until all plugins finish. An exception, invalid result, or unsuccessful result terminates
the sequence and clears all temporary artifacts.

## Execution Ownership

A Kernel instance owns at most one active pipeline. Recursive or concurrent entry is rejected
without waiting. This fail-fast rule prevents a plugin-created thread from waiting on progress that
can only be made by the pipeline currently waiting for that thread.
