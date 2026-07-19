# Modoroco Foundation, Architecture, DevOps, Legal, and Initial Implementation Master Prompt

## Role

Act as the principal software architect, senior Python engineer, DevOps engineer, API designer, database engineer, security engineer, technical writer, and GitHub project maintainer for **Modoroco**.

You are working directly inside the Modoroco repository, now owned by **The 1807 organization**.

Your responsibility is not to create a generic starter template. You must inspect the repository, establish a production-grade architecture, configure the complete engineering workflow, create the required documentation and governance files, and implement a functional vertical foundation of the Modoroco microservice.

Proceed without waiting for approval between phases. Make reasonable architectural decisions, document them, implement them, test them, and report them clearly.

---

# 1. Product Context

Modoroco is a reusable Pomodoro timer engine, API, worker service, and integration platform.

It must support multiple Pomodoro families rather than only one fixed 25-minute timer.

Timer families may include:

* Classic Pomodoro
* Deep work
* Study sessions
* Short focus cycles
* Long focus cycles
* Hydration-focused routines
* Exercise intervals
* Recovery routines
* User-defined routines
* Application-defined routines

Modoroco will be developed independently from Hydrion.

Hydrion will consume Modoroco in a future release through a stable API and generated Dart client package. Other mobile, desktop, web, command-line, embedded, and backend applications must also be able to use Modoroco without depending on Hydrion.

Modoroco must remain product-neutral. Hydrion-specific business rules must never be embedded directly into the Modoroco domain engine.

---

# 2. Primary Mission

Complete the following work:

1. Inspect and understand the existing repository.
2. Confirm or establish the technology stack.
3. Define and document a robust architecture.
4. Configure GitHub repository governance and project-management features.
5. Configure Docker and GitHub Actions CI/CD.
6. Create the legal and open-source governance document stack.
7. Design the complete API and worker blueprint.
8. Implement a functional vertical foundation of the microservice.
9. Demonstrate how Hydrion and other platforms will integrate with Modoroco.
10. Create a complete GitHub Project Kanban board covering all work through the first tested container deployment.
11. Validate the implementation locally.
12. Commit the work in logical checkpoints.
13. Produce a precise final engineering report.

Do not stop after writing documentation. The repository must contain working software.

---

# 3. Non-Negotiable Engineering Rules

## 3.1 No generic scaffolding

Do not produce placeholder implementations, fake adapters, empty service classes, unimplemented interfaces, decorative abstractions, or meaningless health checks.

Do not leave:

* `TODO`
* `FIXME`
* `pass`
* `NotImplementedError`
* Empty exception handlers
* Stubbed repository methods
* Hardcoded successful responses
* Fake test assertions
* Disabled tests without a documented technical reason
* Secrets committed into the repository

Every included component must serve an actual architectural purpose.

## 3.2 Repository safety

Before modifying anything:

* Inspect the current branch.
* Inspect the Git status.
* Inspect the repository structure.
* Inspect existing configuration, documentation, workflows, and source files.
* Record the starting commit.
* Do not modify or force-push `main`.
* Create and work on a dedicated branch named:

`codex/modoroco-foundation`

If that branch already exists, safely continue from it.

Do not delete existing work unless it is clearly obsolete, duplicated, broken, or replaced by a documented migration.

## 3.3 Timer correctness

Never implement active timers by decrementing an integer every second on the server.

A running timer must be calculated from authoritative UTC timestamps.

The timer domain should use fields equivalent to:

* `started_at`
* `expected_end_at`
* `paused_at`
* `total_paused_duration`
* `current_phase_index`
* `state`
* `version`
* `completed_at`
* `cancelled_at`
* `next_transition_at`

The visible countdown is calculated from server timestamps. Clients may render the countdown locally and synchronize periodically.

This design must survive:

* API restarts
* Worker restarts
* Container restarts
* Client disconnections
* Network retries
* Duplicate commands
* Multiple client devices
* Clock drift
* Concurrent requests

## 3.4 Time handling

Use timezone-aware UTC timestamps internally.

Do not store naive datetimes.

Introduce an injectable clock abstraction for deterministic testing.

Tests must not depend on real sleeping.

## 3.5 Architecture discipline

The domain layer must not depend on:

* FastAPI
* SQLAlchemy
* PostgreSQL
* Redis
* Docker
* Hydrion
* HTTP
* Environment variables
* Logging frameworks

Infrastructure must depend inward toward the application and domain layers.

---

# 4. Preferred Technology Stack

Inspect the repository first. If no conflicting implementation already exists, establish the following stack.

## Runtime and application

* Python 3.13
* `uv` for project and dependency management
* `pyproject.toml`
* Committed `uv.lock`
* FastAPI
* Pydantic v2
* Uvicorn
* SQLAlchemy 2 async
* asyncpg
* Alembic
* PostgreSQL
* Server-Sent Events for initial realtime event delivery
* Redis reserved for later distributed coordination and fanout

## Quality and testing

* pytest
* pytest-asyncio
* Hypothesis
* Testcontainers or equivalent isolated PostgreSQL integration testing
* Ruff for formatting and linting
* Pyright in strict mode
* Coverage reporting
* Architecture-boundary tests

## Operations

* Docker
* Docker Compose
* Multi-stage Dockerfile
* GitHub Actions
* GitHub Container Registry
* Structured JSON logging
* OpenTelemetry-compatible instrumentation
* Prometheus-compatible metrics
* OpenAPI 3.1

Do not introduce Kubernetes, Kafka, RabbitMQ, Celery, GraphQL, or multiple databases during the foundation phase unless the existing repository already has a justified dependency on them.

Docker is the deployable artifact environment. GitHub Actions is the CI/CD orchestration platform.

---

# 5. Target Repository Architecture

Create or adapt toward a structure equivalent to:

```text
modoroco/
├── .github/
│   ├── ISSUE_TEMPLATE/
│   ├── workflows/
│   ├── CODEOWNERS
│   ├── PULL_REQUEST_TEMPLATE.md
│   └── dependabot.yml
├── docs/
│   ├── architecture/
│   ├── api/
│   ├── integrations/
│   ├── legal/
│   ├── operations/
│   ├── project/
│   └── adr/
├── migrations/
├── src/
│   └── modoroco/
│       ├── domain/
│       ├── application/
│       ├── infrastructure/
│       ├── interfaces/
│       ├── runtime/
│       └── shared/
├── tests/
│   ├── unit/
│   ├── integration/
│   ├── contract/
│   ├── architecture/
│   └── system/
├── scripts/
├── compose.yaml
├── Dockerfile
├── pyproject.toml
├── uv.lock
├── LICENSE
├── NOTICE
├── README.md
└── SECURITY.md
```

Use the following responsibilities.

## Domain

Contain pure business concepts:

* Timer families
* Timer family versions
* Phase definitions
* Sessions
* Session states
* Commands
* Domain events
* Transition rules
* Duration validation
* Timer calculations
* Domain errors
* Clock protocol

## Application

Contain use cases and orchestration:

* Create timer family
* Publish timer family version
* Create session
* Start session
* Pause session
* Resume session
* Skip phase
* Extend phase
* Complete phase
* Cancel session
* Retrieve session
* List session events
* Process due transitions
* Dispatch outbox events

## Infrastructure

Contain technical adapters:

* SQLAlchemy models
* PostgreSQL repositories
* Unit-of-work implementation
* Alembic migrations
* API-key persistence
* Idempotency persistence
* Transactional outbox
* Structured logging
* Metrics
* Configuration loading

## Interfaces

Contain external boundaries:

* FastAPI routes
* Request and response schemas
* API error mapping
* Authentication dependencies
* SSE event stream
* OpenAPI customization

## Runtime

Contain executable composition:

* API application factory
* Worker entry point
* Dependency wiring
* Graceful startup and shutdown
* Health and readiness checks

---

# 6. Domain Blueprint

## 6.1 Timer family

Model a timer family as a reusable, versioned routine definition.

A family version must contain:

* Family identifier
* Version number
* Name
* Description
* Ordered phase definitions
* Repeat policy
* Long-break policy
* Automatic transition policy
* Customization constraints
* Visibility
* Ownership
* Metadata
* Creation timestamp
* Publication status

An active session must retain the exact family version used when the session began.

Changing a family must not mutate previously started sessions.

## 6.2 Phase definition

Each phase should support:

* Stable phase key
* Display name
* Phase type
* Duration
* Whether it is skippable
* Whether it is extendable
* Minimum duration
* Maximum duration
* Automatic completion behavior
* Notification metadata
* Integration metadata

Initial phase types should include:

* Focus
* Short break
* Long break
* Custom

## 6.3 Session state machine

Use an explicit state machine.

Supported session states should include:

* Created
* Running
* Paused
* Completed
* Cancelled
* Expired

Do not model state through unrelated Boolean columns.

Supported commands should include:

* Start
* Pause
* Resume
* Skip phase
* Extend phase
* Complete current phase
* Cancel
* Restart

Every command must be validated against the current state.

Invalid transitions must return typed domain errors and suitable API responses.

## 6.4 Optimistic concurrency

Every session must have a monotonically increasing version.

Mutating commands must include the expected version.

Conflicting commands must fail safely rather than silently overwriting state.

## 6.5 Idempotency

Mutating API operations must support an `Idempotency-Key`.

The idempotency record should be scoped by:

* Tenant
* API client
* Operation
* Idempotency key

Replayed requests must return the original successful result where appropriate.

## 6.6 Domain events

Create typed events for meaningful changes, including:

* Session created
* Session started
* Session paused
* Session resumed
* Phase completed
* Phase skipped
* Phase extended
* Session completed
* Session cancelled
* Family created
* Family version published

Do not generate one event every second.

---

# 7. Persistence and Worker Blueprint

## 7.1 PostgreSQL authority

PostgreSQL is the authoritative source of truth.

Create normalized persistence for:

* Tenants
* API clients
* Hashed API keys
* Timer families
* Timer family versions
* Phase definitions
* Sessions
* Session phase history
* Commands
* Idempotency records
* Domain events
* Outbox records
* Worker leases or claim metadata

## 7.2 Transactional outbox

When application state changes, persist the state change and corresponding event in the same database transaction.

The worker must process pending outbox records.

Outbox records should support:

* Pending state
* Processing state
* Delivered state
* Failed state
* Retry count
* Next retry timestamp
* Last error
* Created timestamp
* Delivered timestamp

Use bounded retries and deterministic backoff.

## 7.3 Due-session processing

The worker must detect sessions whose `next_transition_at` has elapsed.

It must:

1. Claim due sessions safely.
2. Lock or version-check the session.
3. Recalculate authoritative state.
4. Apply the next valid domain transition.
5. Persist the new session state.
6. Record phase history.
7. Create domain and outbox events.
8. Commit atomically.
9. Avoid duplicate completion during concurrent worker execution.

Use PostgreSQL-safe claiming such as row locking with `SKIP LOCKED` or another documented concurrency-safe mechanism.

## 7.4 Worker process

Create a separately executable worker process using the same application and domain packages as the API.

The worker must include:

* Graceful shutdown
* Configurable polling interval
* Bounded batch size
* Structured logs
* Retry boundaries
* Readiness state
* Database connectivity checks
* No uncontrolled infinite task creation

The API and worker are separate runtime processes, not separate repositories.

---

# 8. API Blueprint and Initial Functional Routes

Implement versioned REST routes.

At minimum:

```text
GET    /live
GET    /ready
GET    /metrics

POST   /v1/families
GET    /v1/families
GET    /v1/families/{family_id}
POST   /v1/families/{family_id}/versions

POST   /v1/sessions
GET    /v1/sessions/{session_id}
POST   /v1/sessions/{session_id}/commands
GET    /v1/sessions/{session_id}/events
GET    /v1/sessions/{session_id}/stream
```

The session command route must support the typed commands defined by the domain.

Use consistent response envelopes only where they improve correctness. Do not wrap every payload in meaningless generic structures.

Define a stable error contract containing:

* Error code
* Human-readable message
* Correlation identifier
* Relevant field details
* Current session version where conflicts occur

Generate accurate OpenAPI documentation from the actual routes and schemas.

Store a generated or validated OpenAPI artifact under the repository.

---

# 9. Authentication and Multi-Application Use

Implement a practical service-to-service authentication foundation.

Use API keys for the first version.

Requirements:

* Never store raw API keys.
* Store a secure hash or keyed digest.
* Show a raw key only at creation time.
* Associate keys with tenants and integration clients.
* Support key revocation.
* Support key status.
* Record creation and last-used timestamps.
* Never log raw credentials.

Add authorization boundaries so one tenant cannot access another tenant's families, sessions, commands, or events.

Create a secure development bootstrap mechanism through environment configuration or a development-only initialization command.

Do not commit a default production API key.

---

# 10. Hydrion and External Platform Integration

Create:

`docs/integrations/hydrion.md`

Explain concretely how Hydrion will use Modoroco.

The integration flow should include:

1. Hydrion authenticates as an integration client.
2. Hydrion discovers available timer families.
3. Hydrion creates or selects a hydration-focused family.
4. Hydrion creates a timer session.
5. Hydrion sends start, pause, resume, skip, extend, and cancel commands.
6. Hydrion renders the countdown locally from `expected_end_at`.
7. Hydrion periodically synchronizes session state.
8. Hydrion listens for meaningful events through SSE.
9. Hydrion maps break events to hydration reminders.
10. Hydrion records water intake through Hydrion's own hydration domain.
11. Modoroco remains unaware of Hydrion's internal hydration repository.

Document how another platform would use the same API without Hydrion-specific assumptions.

Create an SDK strategy covering:

* Dart
* Python
* TypeScript

The OpenAPI contract must be suitable for generated client libraries.

If SDK generation tooling is included, configure it reproducibly. Do not commit a fake client containing manually invented response types that can drift from the API.

---

# 11. Docker Foundation

Create a production-oriented multi-stage Dockerfile.

Requirements:

* Build dependencies excluded from final image
* Non-root runtime user
* Minimal runtime image
* Pinned dependencies
* Deterministic install using `uv.lock`
* Health check
* Graceful termination
* No development server flags in production
* No secrets copied into the image
* Suitable labels and metadata
* API and worker executable from the same image through different commands

Create `compose.yaml` containing:

* `api`
* `worker`
* `postgres`

Add Redis only if it is actually implemented and used.

Compose requirements:

* PostgreSQL health check
* API readiness dependency
* Worker database dependency
* Named persistent volume
* Isolated service network
* Environment file support
* Migration execution strategy
* Restart policy appropriate for local integration testing
* No hardcoded production secrets

Create:

* `.env.example`
* `docs/operations/local-development.md`
* `docs/operations/docker-deployment.md`
* `docs/operations/database-migrations.md`

The complete local environment must start through Docker Compose.

---

# 12. GitHub Repository Configuration

Create the following issue forms.

## 12.1 User story form

Create:

`.github/ISSUE_TEMPLATE/user_story.yml`

Fields must include:

* Story title
* Persona
* User need
* Business value
* Context
* Acceptance criteria
* Dependencies
* Technical considerations
* Security considerations
* Observability requirements
* Test requirements
* Definition of done
* Priority
* Area
* Target milestone

## 12.2 Bug report form

Create:

`.github/ISSUE_TEMPLATE/bug_report.yml`

Include:

* Description
* Expected behavior
* Actual behavior
* Reproduction steps
* Environment
* Modoroco version
* API or worker component
* Logs
* Correlation ID
* Severity
* Data-integrity impact
* Security impact

## 12.3 Feature request form

Create:

`.github/ISSUE_TEMPLATE/feature_request.yml`

Include:

* Problem
* Proposed solution
* Alternatives
* API impact
* Worker impact
* Persistence impact
* Compatibility impact
* Security impact
* Operational impact
* Acceptance criteria

## 12.4 Architecture proposal form

Create:

`.github/ISSUE_TEMPLATE/architecture_proposal.yml`

Use this for changes affecting contracts, storage, concurrency, authentication, worker behavior, deployment, or infrastructure.

## 12.5 Pull request template

Create:

`.github/PULL_REQUEST_TEMPLATE.md`

Include:

* Summary
* Linked issue
* Change type
* Architecture impact
* API compatibility
* Database migration
* Security review
* Tests added
* Documentation updated
* Rollback plan
* Validation commands
* Checklist

## 12.6 Other repository files

Create and configure:

* `.github/CODEOWNERS`
* `.github/dependabot.yml`
* `.github/ISSUE_TEMPLATE/config.yml`
* Label taxonomy documentation
* Branching strategy
* Conventional commit guidance
* Release process
* Semantic versioning policy

Recommended labels:

* `type:feature`
* `type:bug`
* `type:user-story`
* `type:architecture`
* `type:security`
* `type:documentation`
* `type:devops`
* `area:domain`
* `area:api`
* `area:worker`
* `area:database`
* `area:sdk`
* `area:docker`
* `area:ci`
* `priority:critical`
* `priority:high`
* `priority:medium`
* `priority:low`
* `status:blocked`

Create labels through the GitHub CLI if authentication and permissions allow.

---

# 13. GitHub Actions CI/CD

Create focused workflows rather than one oversized workflow.

## 13.1 Continuous integration

Create:

`.github/workflows/ci.yml`

Run on:

* Pull requests targeting `main`
* Pushes to `main`
* Manual dispatch

Include:

1. Checkout
2. Python setup
3. `uv` setup
4. Locked dependency installation
5. Ruff formatting validation
6. Ruff lint validation
7. Pyright strict validation
8. Unit tests
9. Architecture tests
10. PostgreSQL integration tests
11. Migration validation
12. Coverage generation
13. Docker image build
14. Docker Compose smoke test
15. OpenAPI contract validation

Use concurrency cancellation for superseded runs.

Use dependency caching safely.

Do not run duplicate workflows for both the source branch push and pull request unless intentionally required.

## 13.2 Security workflow

Create:

`.github/workflows/security.yml`

Include appropriate available checks such as:

* Dependency review
* CodeQL
* Secret detection
* Dependency vulnerability scanning
* Container vulnerability scanning
* SBOM generation

Use maintained GitHub Actions pinned to safe versions or commit SHAs where practical.

## 13.3 Container publishing

Create:

`.github/workflows/container.yml`

Run on:

* Semantic version tags
* Manual dispatch

Build the image and publish it to GitHub Container Registry.

Apply tags for:

* Exact version
* Major and minor version
* Commit SHA
* `latest` only for stable releases

Generate provenance and SBOM where supported.

## 13.4 Release workflow

Create:

`.github/workflows/release.yml`

Create a GitHub Release from semantic version tags.

Include:

* Release notes
* Changelog verification
* Image reference
* Migration notes
* Compatibility notes
* Known limitations

Do not configure automatic deployment to an unknown hosting provider.

The first deployment target for this foundation is:

* A locally validated Docker Compose environment
* A publishable production container image
* A GitHub Container Registry release artifact

Document the future remote deployment interface without pretending that a public environment exists.

---

# 14. Legal and Governance Document Stack

Use Apache License 2.0 unless the repository already contains a deliberate conflicting licensing decision.

Create:

* `LICENSE`
* `NOTICE`
* `CONTRIBUTING.md`
* `CODE_OF_CONDUCT.md`
* `SECURITY.md`
* `TRADEMARK.md`
* `SUPPORT.md`
* `CHANGELOG.md`
* `docs/legal/privacy-policy.md`
* `docs/legal/terms-of-service.md`
* `docs/legal/api-acceptable-use-policy.md`
* `docs/legal/third-party-notices.md`
* `docs/legal/data-retention.md`
* `docs/legal/responsible-disclosure.md`

Requirements:

* Identify Modoroco as a project of The 1807 organization where appropriate.
* Clearly distinguish open-source self-hosting from any future hosted Modoroco service.
* Do not falsely claim that Modoroco currently collects, sells, or processes data that is not implemented.
* Clearly identify sections that require legal review before a hosted commercial launch.
* Explain API-user responsibilities.
* Explain that trademark rights are separate from the Apache software license.
* Use a Developer Certificate of Origin contribution model initially unless a CLA is already required.
* Include SPDX license identifiers in appropriate source and configuration files.
* Generate third-party notices from actual dependencies rather than inventing packages.

Do not present generated legal text as a substitute for professional legal review.

---

# 15. Architecture Documentation

Create the following documents.

## Core architecture

* `docs/architecture/system-overview.md`
* `docs/architecture/domain-model.md`
* `docs/architecture/state-machine.md`
* `docs/architecture/api-worker-boundary.md`
* `docs/architecture/persistence-model.md`
* `docs/architecture/idempotency.md`
* `docs/architecture/concurrency.md`
* `docs/architecture/security-model.md`
* `docs/architecture/observability.md`
* `docs/architecture/failure-recovery.md`

## API

* `docs/api/api-conventions.md`
* `docs/api/error-contract.md`
* `docs/api/versioning.md`
* `docs/api/authentication.md`
* `docs/api/realtime-events.md`

## Architecture decision records

At minimum create ADRs for:

1. Python and FastAPI selection
2. PostgreSQL as source of truth
3. Timestamp-based timer calculation
4. Transactional outbox
5. API and worker in one repository
6. SSE before WebSockets
7. API-key authentication foundation
8. Redis deferred until distributed requirements exist
9. Apache-2.0 licensing
10. OpenAPI-driven SDK generation

ADRs must include:

* Context
* Decision
* Alternatives considered
* Consequences
* Status

---

# 16. Initial Functional Vertical Slice

Implement enough functionality to prove the architecture is real.

The vertical slice must support:

1. Starting PostgreSQL.
2. Running migrations.
3. Starting the API.
4. Starting the worker.
5. Authenticating with a development integration client.
6. Creating a timer family.
7. Publishing a timer family version.
8. Creating a timer session.
9. Starting the session.
10. Pausing the session.
11. Resuming the session.
12. Skipping a phase.
13. Extending a phase.
14. Cancelling a session.
15. Retrieving the authoritative session state.
16. Retrieving session events.
17. Processing an automatically completed phase through the worker.
18. Recovering an active timer after an API or worker restart.
19. Rejecting stale session versions.
20. Replaying an idempotent request safely.
21. Preventing cross-tenant data access.
22. Exposing liveness, readiness, and metrics endpoints.

The implementation must use the real domain, application, database, API, and worker layers.

Do not mock the database in integration tests.

---

# 17. Testing Requirements

Create a complete initial test suite.

## Unit tests

Test:

* Every valid state transition
* Every invalid state transition
* Duration validation
* Family-version immutability
* Timer calculations
* Pause accumulation
* Resume calculations
* Phase completion
* Session completion
* Cancellation
* Extension limits
* Clock injection
* Domain event generation

## Stateful tests

Use Hypothesis state-machine testing for command sequences such as:

* Start
* Pause
* Resume
* Pause again
* Extend
* Skip
* Complete
* Cancel

Validate invariants:

* Remaining time is never negative
* Completed sessions cannot restart without an explicit restart operation
* Cancelled sessions cannot receive active commands
* Version increases after successful mutations
* Duplicate idempotent commands do not duplicate events
* Phase index remains valid
* Total paused time never decreases

## Integration tests

Test:

* PostgreSQL repositories
* Alembic migrations
* Unit of work
* Optimistic concurrency
* Idempotency
* Tenant isolation
* Worker claims
* Concurrent workers
* Outbox retries
* API authentication
* API error responses
* SSE event delivery
* Restart recovery

## System tests

Validate through Docker Compose:

* Database starts
* Migration succeeds
* API becomes ready
* Worker becomes ready
* Functional session lifecycle succeeds
* Container restart preserves active sessions
* Invalid credentials are rejected

No test should wait for a real Pomodoro duration.

---

# 18. Observability

Implement:

* Structured JSON logs
* Correlation IDs
* Request IDs
* Tenant and client context without exposing secrets
* API latency metrics
* Command counters
* State-transition counters
* Active-session gauge
* Worker batch metrics
* Worker failure metrics
* Outbox backlog
* Database connectivity status
* Readiness status

Health behavior:

* `/live` confirms the process is alive.
* `/ready` confirms required dependencies are available.
* `/metrics` exposes machine-readable metrics.

Do not make `/live` dependent on PostgreSQL.

Do not expose sensitive configuration through health endpoints.

---

# 19. GitHub Project Kanban Board

Create a GitHub Project for Modoroco using available GitHub authentication.

Suggested project name:

`Modoroco v0.1 Foundation`

Create views or workflow statuses for:

* Backlog
* Ready
* In Progress
* Review
* Blocked
* Done

Create fields for:

* Type
* Priority
* Area
* Milestone
* Effort
* Release
* Owner

Create milestones:

1. Architecture and repository foundation
2. Domain engine
3. Persistence and migrations
4. API foundation
5. Worker foundation
6. Authentication and tenant isolation
7. Docker and CI
8. Integration contract
9. First system test
10. First container release

Create issues or user stories covering every implemented and remaining task through the first container deployment.

The board must include at least the following epics:

* Repository foundation
* Architecture
* Timer domain
* Family versioning
* Session state machine
* Persistence
* Idempotency
* Worker scheduling
* Transactional outbox
* API authentication
* Tenant isolation
* REST API
* SSE events
* OpenAPI
* Dart integration contract
* Docker
* CI
* Security scanning
* Observability
* Legal
* Documentation
* Testing
* GHCR publishing
* First release

Every issue must have:

* Clear objective
* Acceptance criteria
* Dependencies
* Area
* Priority
* Milestone
* Definition of done

Link issues to the project and assign appropriate statuses.

If GitHub Project creation is blocked by missing organization project permissions, do not silently skip it.

Instead:

1. Create all issues that permissions allow.
2. Create `docs/project/kanban-plan.md`.
3. Create `docs/project/issue-manifest.md`.
4. Record the exact permission failure.
5. Provide the exact remaining manual operation required.

---

# 20. README Requirements

Rewrite or create a professional `README.md`.

Include:

* Modoroco identity
* The 1807 ownership
* Product purpose
* Core capabilities
* Architecture summary
* Technology stack
* Repository layout
* Local installation
* Docker Compose startup
* Migration commands
* API startup
* Worker startup
* Testing commands
* OpenAPI location
* Authentication model
* Hydrion integration summary
* Contribution guidance
* Security reporting
* License
* Current project status

Do not advertise unimplemented features as complete.

Clearly distinguish:

* Implemented
* Foundation complete
* Planned
* Deferred

---

# 21. Development and Commit Strategy

Use logical commits.

Suggested checkpoints:

1. Repository and tooling foundation
2. Architecture and ADR documentation
3. Domain engine and tests
4. Persistence and migrations
5. API and authentication
6. Worker and outbox
7. Docker and local operations
8. GitHub workflows and governance
9. Legal documentation
10. Kanban and backlog
11. Final hardening and verification

Use conventional commit messages.

Do not create one giant unreviewable commit.

Do not push or merge into `main`.

---

# 22. Required Validation

Run all applicable validations before completion.

At minimum:

```text
uv sync --locked --all-extras --dev
ruff format --check .
ruff check .
pyright
pytest
alembic upgrade head
docker build .
docker compose config
docker compose up
```

Also validate:

* API imports
* Worker imports
* `/live`
* `/ready`
* `/metrics`
* OpenAPI generation
* Migration from an empty database
* Migration repeatability
* Docker restart recovery
* Worker phase transition
* Idempotency replay
* Optimistic-concurrency conflict
* Tenant isolation
* Clean Git status after final commit

Do not claim a validation passed unless it was actually run.

If a validation cannot be run because of credentials, permissions, unavailable Docker, or unavailable network access, report it as blocked with the exact reason.

---

# 23. Definition of Done

This assignment is complete only when:

* The stack is established and documented.
* The architecture is implemented, not merely described.
* The timer domain is functional.
* PostgreSQL persistence is functional.
* Alembic migrations are functional.
* The API is functional.
* The worker is functional.
* The transactional outbox is functional.
* Idempotency is functional.
* Optimistic concurrency is functional.
* API-key authentication is functional.
* Tenant isolation is tested.
* Docker image builds.
* Docker Compose runs the service.
* CI workflows are valid.
* Security workflows exist.
* GHCR publishing workflow exists.
* Legal and governance documents exist.
* Hydrion integration is documented.
* OpenAPI is generated from real routes.
* The initial test suite passes.
* The Kanban board or complete permission-blocked fallback is created.
* The working tree is clean.
* Work is committed on the dedicated branch.

---

# 24. Final Response Format

At completion, provide a factual report containing:

1. Executive summary
2. Starting branch and commit
3. Final branch and commit
4. Repository findings
5. Final technology stack
6. Architecture decisions
7. Implemented functionality
8. API routes
9. Worker behavior
10. Database and migration summary
11. Authentication and tenant model
12. Docker and Compose summary
13. GitHub Actions created
14. GitHub templates and governance created
15. Legal documents created
16. Hydrion integration design
17. Kanban board status
18. Issues and milestones created
19. Test totals
20. Validation commands and results
21. Security findings
22. Known limitations
23. Deferred work
24. Permission or credential blockers
25. Working-tree status
26. Recommended next engineering milestone

Be exact.

Do not report generic statements such as "the project is production-ready" without evidence.

Do not conceal failures, skipped validation, missing permissions, or incomplete components.
