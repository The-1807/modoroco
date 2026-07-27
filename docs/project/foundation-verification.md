# Foundation verification — 2026-07-27

Baseline `30eebb6da1f758e5fd9a39c954b559e02a7f6f4d` was verified on
`chore/foundation-verification`. Eleven unrelated unstaged deletions were present before the work
and were preserved outside the hardening commit.

## Completed

- `uv sync --locked --all-extras --dev`: 54 packages resolved, 53 checked, exit 0.
- Strict Pyright reduced from 98 errors to zero without exclusions or suppression.
- Ruff formatting and linting pass.
- Thirteen deterministic tests pass with 76% aggregate coverage.
- API-key authentication is represented by an OpenAPI security scheme.
- Family and command idempotency bind keys to canonical request payloads and reject conflicts.
- Two-tenant access tests verify family discovery and mutation isolation.
- A worker `--check` command performs a real database query for container health.
- Alembic upgrade/repeat/downgrade behavior was exercised against local SQLite.
- OpenAPI generation and immediate drift check are deterministic.
- GitHub labels, milestones, issues, and organization Project 5 were created.

## Blocked, not passed

Docker, Compose, PostgreSQL locking tests, two-worker claims, automatic transitions against
PostgreSQL, and container/API/worker restart persistence could not run: Docker, Podman, nerdctl,
`psql`, and a PostgreSQL Windows service are absent. SQLite results are not treated as substitutes.

Project custom field `Type` was rejected because GitHub reserves the name. Custom project-view
creation is not exposed by the available GitHub CLI/GraphQL interfaces.
