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

## Hosted PostgreSQL and container verification — 2026-07-27

The local Docker prerequisite above remains an accurate record of the workstation limitation, but
it no longer blocks foundation verification.

### Execution identity

- Workflow: `.github/workflows/postgresql-container-verification.yml`
- Workflow run: <https://github.com/The-1807/modoroco/actions/runs/30303320850>
- Run ID: `30303320850`
- Tested commit: `e126a81748dfc843b6847fc87916d64318aa17e1`
- Runner: Ubuntu 24.04, Linux `6.17.0-1020-azure`
- Quality Python: CPython 3.13.14
- Runtime-image Python: CPython 3.13.5
- PostgreSQL: 18.4
- Docker Engine client/server: 28.0.4, API 1.48
- Docker Compose: 2.38.2
- Image: `modoroco:gha-verification-e126a81748dfc843b6847fc87916d64318aa17e1`
- Image ID and size: `sha256:ca2d6b33fbe4180ff218a3adc95dab9bf5d4b12b8603c65634637eb97b62e43c`,
  853 MB
- Runtime user: `modoroco` (verified non-root)

### Results

- Quality: passed; locked sync, Ruff format/lint, strict Pyright with zero errors, 14 tests passed
  and one explicitly PostgreSQL-gated test skipped in the local suite.
- PostgreSQL integration: passed; empty-database upgrade, repeat upgrade, current head, schema,
  indexes, constraints, foreign keys, and one focused PostgreSQL concurrency test.
- Docker image: passed; build, inspection, history, non-root execution, Python and package import
  smoke tests, health-check metadata, and secret-pattern inspection.
- Compose: passed with PostgreSQL, one successful migration container, API, and two healthy worker
  instances on isolated backend and API-edge networks.
- API liveness, readiness, metrics, worker readiness, automatic transition, phase history,
  transactional outbox delivery/retry, idempotent replay/conflict, stale-version rejection,
  tenant isolation, concurrent worker claims, API restart, worker restart, database outage
  recovery, full-stack restart, named-volume persistence, container authentication, SSE, and
  deterministic OpenAPI checks: passed.
- The full-stack restart retained the named PostgreSQL volume until persistence evidence was
  collected; cleanup removed it only afterward.

Artifacts retained for 14 days are `quality-python-313`, `postgresql-integration`, `docker-image`,
`compose-system`, and `verification-summary`. They contain command/test output, migration and
schema evidence, image inspection/history, Docker/Compose/PostgreSQL versions, Compose service and
network/volume state, logs, structured system-stage results, cleanup evidence, and the final
machine-readable gate.

### Findings, warnings, and earlier failed runs

The hosted execution found and verified fixes for transactional Alembic execution, PostgreSQL FK
insert ordering, PostgreSQL 18's volume layout, relocatable container entry points, runtime
migration packaging, bootstrap ordering, and isolated API ingress. No credential or raw API-key
leak was found.

Earlier runs were preserved rather than hidden:

- `30299865733`: secret scan matched documented placeholders and its own rule.
- `30299978699`: PostgreSQL transactional DDL rolled back.
- `30300325605` and `30300540251`: real foreign keys exposed fixture and session/event ordering.
- `30300778902`: PostgreSQL 18 rejected the legacy data-volume mount.
- `30301240332` and `30301498048`: relocated virtualenv entry points and flattened migrations
  made the migration container fail.
- `30301904855`: bootstrap client insertion preceded its tenant.
- `30302257143`: the API was attached only to an internal network, preventing host ingress.

GitHub emitted Node.js 20 deprecation warnings for current action major versions and forced those
actions to Node.js 24; the actions completed successfully. No GitHub infrastructure error remains.
Docker Desktop's local Linux-engine HTTP 500/startup limitation remains workstation-specific.
