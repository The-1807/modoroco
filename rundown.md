Modoroco in Python as a modular monorepo containing a reusable core package and one deployable microservice.

Core stack

Language	Python 3.13
Dependency management	uv with pyproject.toml and committed uv.lock
Core timer engine	Pure Python domain package
API framework	FastAPI
Validation and schemas	Pydantic v2
ASGI server	Uvicorn
Primary database	PostgreSQL 18
Database layer	SQLAlchemy 2.0 async
PostgreSQL driver	asyncpg
Migrations	Alembic
Realtime delivery	SSE initially, WebSockets when required
Cache and coordination	Redis, added when scaling requires it
Background processing	Separate async worker using a PostgreSQL outbox
Containerization	Docker with multi-stage builds
Local orchestration	Docker Compose
Testing	pytest, pytest-asyncio, Hypothesis, Testcontainers
Linting and formatting	Ruff
Static typing	Pyright strict mode
Observability	OpenTelemetry, Prometheus metrics, structured JSON logging
CI/CD	GitHub Actions
Image registry	GitHub Container Registry
API specification	OpenAPI 3.1
Hydrion integration	Generated Dart SDK


FastAPI already supports typed API development and WebSockets, while SQLAlchemy 2.0 provides stable async database support. Alembic remains the appropriate migration system for SQLAlchemy projects. 

uv is the right dependency tool because it manages the project environment and produces a cross-platform lockfile that can be committed for reproducible installations and Docker builds. 

Repository architecture

Modoroco should be one repository with separately publishable and deployable components:

modoroco/
├── packages/
│   ├── modoroco-core/
│   └── modoroco-client-python/
├── services/
│   ├── api/
│   └── worker/
├── sdks/
│   └── dart/
├── migrations/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   └── stateful/
├── docker/
├── openapi/
├── pyproject.toml
├── uv.lock
├── Dockerfile
└── compose.yaml

This is not multiple independent microservices. It is one Modoroco service with two runtime processes:

modoroco-api

modoroco-worker


They share the same core package, domain rules, schemas, and database.

The most important timer decision

Never run Modoroco by decrementing a server-side integer every second.

A running session should store authoritative timestamps and state:

started_at

expected_end_at

paused_at

accumulated_pause_duration

completed_at

current_phase

state

version


The client calculates the visible countdown from expected_end_at and periodically synchronizes with the server. This prevents timer drift, reduces server traffic, survives disconnected clients, and allows recovery after container restarts.

The API should send:

Current server time

Authoritative session state

Current phase

Expected phase completion time

Session version


Hydrion then renders the countdown locally without requesting a new value every second.

Pomodoro families model

Your main domain object should be TimerFamily.

A family defines:

Family name and version

Ordered phases

Focus duration

Break durations

Long-break frequency

Automatic or manual transitions

Repeat rules

Allowed customizations

Notification rules

Completion rules

Hydration integration metadata

Visibility and ownership


The main domain entities should be:

TimerFamily

TimerFamilyVersion

TimerPhaseDefinition

TimerPreset

TimerSession

TimerSessionPhase

TimerEvent

SessionCommand

UserPreference

IntegrationClient


Version families instead of modifying active definitions. A session must retain the exact family version with which it started.

State machine

Use an explicit state machine rather than scattered Boolean fields.

Primary session states:

created
scheduled
running
paused
completed
cancelled
expired

Primary commands:

start
pause
resume
skip_phase
extend_phase
complete_phase
cancel
restart

Every command should require:

Session identifier

Expected session version

Idempotency key

Actor identifier

Command timestamp


Optimistic concurrency prevents two devices from pausing, resuming, or completing the same session inconsistently.

Hypothesis is especially suitable here because its stateful testing can generate complete sequences of actions against a state machine, not just individual input values. 

REST and realtime approach

Use REST for commands and authoritative reads:

POST   /v1/families
GET    /v1/families
POST   /v1/sessions
GET    /v1/sessions/{session_id}
POST   /v1/sessions/{session_id}/commands
GET    /v1/sessions/{session_id}/events
DELETE /v1/sessions/{session_id}

Use Server-Sent Events first for session state changes because Modoroco mainly sends updates from server to client.

Use WebSockets later for:

Shared group timers

Collaborative focus rooms

Synchronized family sessions

Real-time host controls

Multi-participant presence


Do not stream one event per second. Stream meaningful transitions such as paused, resumed, phase completed, skipped, extended, or cancelled.

PostgreSQL and Redis responsibilities

PostgreSQL is authoritative

Store:

Families and family versions

Presets

Sessions

Phase history

Commands

Events

Idempotency records

Notification jobs

Integration clients


PostgreSQL is suitable as the source of truth because it provides transactional integrity and fault-tolerant data-management capabilities. 

Redis is optional initially

Add Redis when Modoroco needs:

Distributed rate limiting

Short-lived session caching

Distributed locks

Cross-instance event broadcasting

Connection presence

Realtime fanout

High-volume event consumption


For reliable internal events, prefer Redis Streams rather than plain Pub/Sub. Redis documents that Pub/Sub messages can be missed by disconnected consumers, while Streams persist events and support stronger delivery semantics. 

Do not make Redis the permanent timer database.

Worker design

Use a separate Modoroco worker process for:

Phase-completion notifications

Webhook delivery

Mobile push notification requests

Cleanup and expiration

Analytics aggregation

Event delivery retries


Start with a transactional PostgreSQL outbox. When a session command changes state, write the state change and its outgoing event within the same database transaction. The worker then processes pending outbox records.

This avoids introducing Celery, RabbitMQ, Kafka, or another major infrastructure component before Modoroco actually needs one.

Hydrion integration

Generate the Dart SDK from Modoroco’s committed OpenAPI contract.

Hydrion should depend on the Dart client, not Modoroco’s internal database or Python package.

The Dart SDK should expose:

Family discovery

Session creation

Start, pause, resume, skip, reset, and cancel commands

Session synchronization

Event subscriptions

Authentication

Idempotency handling

Network retry policy

Offline state reconciliation


The Hydrion integration can later attach hydration behavior to family metadata without placing Hydrion-specific logic inside the Modoroco core.

Docker deployment

The production image should use:

Multi-stage build

Minimal runtime image

Non-root user

Read-only application files

Pinned dependencies

Container health check

Separate /live and /ready endpoints

Graceful shutdown

Database migration job

No secrets embedded in the image


Docker recommends multi-stage builds to separate build dependencies from the final runtime image, reducing image size and attack surface. Compose also supports service health checks directly. 

The initial Compose environment should contain:

api
worker
postgres

Add Redis only when realtime fanout, distributed coordination, or higher scale makes it necessary.

Testing standard

Modoroco needs unusually strong timer tests because time, retries, concurrency, and restarts create subtle failures.

Use:

Unit tests for every state transition

Fake injectable clock

Hypothesis state-machine testing

PostgreSQL integration tests

API contract tests

Idempotency tests

Concurrent-command tests

Restart recovery tests

Clock-skew tests

Timezone and daylight-saving tests

Migration upgrade and downgrade tests

Docker health and shutdown tests

Dart SDK compatibility tests


Never use real sleeping or waiting in the core test suite. Time must be advanced through an injected clock.

Observability

Expose:

GET /live
GET /ready
GET /metrics

Record:

Session creation rate

Active sessions

State-transition counts

Command conflicts

Idempotency replays

Worker backlog

Notification failures

API latency

Database latency

SSE or WebSocket connections


OpenTelemetry supports Python traces, metrics, logs, and FastAPI instrumentation, making it suitable for following requests from the API through database and worker operations. 

Final stack decision


Python 3.13 + FastAPI + Pydantic v2 + SQLAlchemy 2.0 async + asyncpg + Alembic + PostgreSQL + Docker + Docker Compose + pytest + Hypothesis + Ruff + Pyright + OpenTelemetry.

will Add Redis only when Modoroco reaches distributed deployment or requires cross-instance realtime fanout.