# Foundation issue manifest

Each item requires measurable acceptance criteria, linked dependencies, tests/docs, and a reviewed
definition of done when created through GitHub.

| Epic | Area | Priority | Milestone | Initial status |
|---|---|---|---|---|
| Repository foundation and architecture | CI | High | Repository/architecture | Done |
| Timer domain and state machine | Domain | Critical | Domain engine | Done |
| Immutable family versioning | Domain | High | Domain engine | Done |
| PostgreSQL persistence and migrations | Database | Critical | Persistence/migrations | Review |
| Idempotency and optimistic concurrency | API | Critical | API | Done |
| Transactional outbox and due scheduling | Worker | Critical | Worker | Review |
| API authentication and tenant isolation | API | Critical | Authentication/isolation | Review |
| REST API, SSE, and OpenAPI | API | High | API | Done |
| Dart/Python/TypeScript generated clients | SDK | High | Integration contract | Backlog |
| Docker and local orchestration | Docker | High | Docker/CI | Blocked |
| CI, security scanning, and GHCR publishing | CI | High | Docker/CI | Review |
| Metrics, traces, and structured logs | API | Medium | API | In Progress |
| Legal, governance, and documentation | Documentation | Medium | Repository/architecture | Review |
| PostgreSQL integration and system testing | Database | Critical | First system test | Blocked |
| First signed container release | Docker | High | First container release | Backlog |

Docker and PostgreSQL system-test items remain blocked locally by the absent Docker executable and
the absence of a local PostgreSQL service. Labels, ten milestones, issues 6–20, and organization
Project 5 were created on 2026-07-27 from this manifest.
