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

## PostgreSQL and container gate — 2026-07-27

### Python 3.13

`uv python install 3.13` installed CPython 3.13.14. The command
`uv sync --python 3.13 --locked --all-extras --dev` completed successfully with 54 packages
resolved and 50 installed into the recreated project environment. Domain, API, worker, database,
desktop, Alembic dependency, and OpenAPI imports succeeded under
`C:\Users\Wildf\OneDrive\Desktop\modoroco\.venv\Scripts\python.exe`.

Under Python 3.13.14:

- `ruff format --check .` passed for 28 files.
- `ruff check .` passed.
- strict `pyright` reported zero errors and zero warnings.
- `pytest -q` passed 13 tests with 76% aggregate coverage.
- OpenAPI drift validation passed.
- The Starlette TestClient emitted its documented upstream `httpx` deprecation warning.

### Docker prerequisite

Docker Desktop 4.84.0 is registered as installed through WinGet. Its CLI is Docker 29.6.2,
context `desktop-linux`, at the user-local Docker Desktop installation. WSL2 2.7.11 and hardware
virtualization are active.

The Linux engine did not become operational. `docker version` returned HTTP 500 from
`dockerDesktopLinuxEngine`, and `docker desktop status --format json` remained `starting` with an
empty session ID for six checks over 30 seconds. Consequently no image, container, network, or
volume was created by this milestone.

The required manual operation is to open Docker Desktop, complete or confirm subscription terms
and WSL2 onboarding, approve any privileged repair, allow any requested Windows restart, and wait
until `docker desktop status` reports `running`. Only then can the image build, Compose startup,
PostgreSQL migrations/integration tests, worker concurrency, automatic transitions, outbox
delivery/retry, and API/worker/volume restart gates be executed. No SQLite result is substituted
for those blocked PostgreSQL checks.

### GitHub Project follow-up

Project <https://github.com/orgs/The-1807/projects/5> remains open with all 15 issues and all ten
milestones. Every item has Status, Priority, Area, Effort, Release, and Owner populated. Status
counts are Backlog 2, Blocked 2, Done 5, In Progress 1, and Review 5. The reserved `Type` field and
custom-view API limitations recorded above are unchanged.
