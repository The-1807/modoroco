# API conventions

The contract is REST under `/v1`, with UUID identifiers, ISO-8601 UTC timestamps, and OpenAPI 3.1.
Mutating session commands require `Idempotency-Key` and `expected_version`. A conflict returns 409;
invalid domain transitions return 422; missing tenant-owned resources return 404 to avoid disclosure.

Errors include a stable code, human message, correlation identifier, and current session version
when relevant. `X-Correlation-ID` is accepted or generated and returned. SSE emits event ID, type,
and JSON data for meaningful state transitions only—not countdown ticks.

