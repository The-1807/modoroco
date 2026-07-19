# Hydrion integration

Hydrion authenticates as its own tenant integration client, discovers or creates a
hydration-oriented family, publishes a phase sequence, and creates a session pinned to that
version. It sends versioned, idempotent start, pause, resume, skip, extend, and cancel commands.

Hydrion renders locally from `expected_end_at`, periodically retrieves the authoritative session,
and subscribes to the session SSE stream. Break events may trigger Hydrion reminders, but water
intake remains in Hydrion's hydration domain. Modoroco never reads Hydrion storage or embeds its
business rules.

Dart, Python, and TypeScript clients will be generated from `openapi/openapi.json`. Generated SDKs
must own retries, credential injection, idempotency-key creation, SSE reconnection, and conflict
reconciliation. Any other platform follows the same product-neutral flow.

