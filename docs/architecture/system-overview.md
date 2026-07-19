# System overview

Modoroco is one product with three runtime surfaces: a native Qt desktop client, an ASGI API,
and an asynchronous worker. PostgreSQL is the sole service authority. The API and worker share
the pure `modoroco.domain` package but are separately executable and deployable from one image.

Dependencies point inward: runtime composes interfaces and infrastructure; interfaces invoke
application use cases; application coordinates domain and repositories; domain imports no web,
database, environment, or logging framework.

Sessions retain the exact immutable family-version identifier and phase snapshot used at
creation. Running time is derived from `expected_end_at` and current UTC time. The worker claims
due rows with `FOR UPDATE SKIP LOCKED`, applies the same aggregate command as the API, and writes
state, events, and outbox messages atomically.

## Trust boundaries

Every protected request authenticates an integration client by SHA-256 API-key digest, resolves
one tenant, and includes that tenant in repository predicates. Raw keys are accepted only in the
request header and are never persisted or logged. Mutations combine optimistic session versions
with a tenant/client/operation-scoped idempotency key.

## Failure model

API or worker restarts do not alter a running timer because no process owns an in-memory tick.
Undelivered outbox records remain durable. Conflicting device commands return HTTP 409 with the
current version. PostgreSQL readiness affects `/ready`, never `/live`.

