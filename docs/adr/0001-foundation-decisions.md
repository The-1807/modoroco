# Foundation decisions

Status: accepted — 2026-07-19

## Runtime and repository

Context: Modoroco needs reusable timer rules and independently scalable request and scheduling
processes. Decision: Python 3.13, FastAPI, Pydantic 2, SQLAlchemy async, and one repository/image
with API and worker commands. Alternatives considered: multiple repositories and synchronous ORM.
Consequence: shared contracts remain consistent while runtime processes scale independently.

## Authority and time

Decision: PostgreSQL is authoritative and timers use UTC timestamps. Alternatives: Redis state or
per-second counters. Consequence: restarts and disconnected clients do not create drift.

## Delivery and coordination

Decision: commit domain events and a PostgreSQL outbox atomically; use SSE before WebSockets; defer
Redis until multi-instance fanout requires it. Alternatives: broker-first architecture and plain
Pub/Sub. Consequence: fewer operational dependencies with durable initial delivery semantics.

## Security, licensing, and SDKs

Decision: use tenant-scoped API-key digests, Apache-2.0, and generated SDKs from committed OpenAPI.
Alternatives: JWT user authentication, proprietary licensing, and handwritten clients.
Consequence: practical service integration, explicit trademark separation, and less contract drift.

