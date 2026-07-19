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

Docker and system-test items are blocked locally by the absent Docker executable. Project creation
is blocked by the absent Git remote, as recorded in `kanban-plan.md`.

