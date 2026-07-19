# Modoroco

Modoroco is The 1807's product-neutral timer engine, integration API, scheduling worker, and
considered native focus environment. It supports immutable, customizable timer families without
embedding Hydrion or another consumer's business rules.

## Implemented foundation

The current vertical slice is a complete PySide6 application with:

- a custom-rendered, animated focus dial;
- focus, short-break, and long-break modes;
- start, pause, resume, reset, and complete interactions;
- timestamp-based countdown calculation that cannot drift with UI load;
- focus insights, curated routines, and persisted preferences;
- keyboard control with `Space` and `R`;
- high-DPI native Qt rendering and platform window integration;
- explicit server session state machine and immutable family versions;
- FastAPI/OpenAPI REST endpoints and meaningful Server-Sent Events;
- async SQLAlchemy persistence, Alembic migration, and PostgreSQL transactional outbox;
- tenant-scoped API-key authentication, idempotency, and optimistic concurrency;
- independently executable due-transition/outbox worker;
- liveness, dependency readiness, correlation IDs, and Prometheus metrics;
- multi-stage non-root container and PostgreSQL Compose environment.

## Run locally

Production and CI target Python 3.13 with `uv` and the committed lockfile.

```powershell
uv sync --locked --all-extras --dev
Copy-Item .env.example .env
# Set unique POSTGRES_PASSWORD and MODOROCO_BOOTSTRAP_API_KEY values.
docker compose up --build
```

The API is available at `http://localhost:8000`; authenticate protected routes with `X-API-Key`.
Run the desktop independently with `uv run modoroco`, migrations with `uv run alembic upgrade head`,
or the processes with `uv run modoroco-api` and `uv run modoroco-worker`.

## Quality checks

```powershell
uv run ruff format --check .
uv run ruff check .
uv run pyright
uv run pytest
uv run python scripts/generate_openapi.py --check
```

The timer domain is independent of Qt and covered by deterministic tests using injected,
timezone-aware timestamps. No test waits on wall-clock time.

## Architecture and repository

`src/modoroco/domain` is pure business logic. Application use cases coordinate it with adapters in
`infrastructure`; `interfaces` owns HTTP; `runtime` composes API and worker executables.
`src/modoroco_ui` is the native client. Migrations, contract, tests, operations, architecture,
governance, and workflows live in their conventional top-level directories.

The actual generated contract is [openapi/openapi.json](openapi/openapi.json). Hydrion integration
is documented in [docs/integrations/hydrion.md](docs/integrations/hydrion.md). Contributors should
read [CONTRIBUTING.md](CONTRIBUTING.md); security reports follow [SECURITY.md](SECURITY.md).

## Status

The vertical foundation is implemented and undergoing pre-1.0 validation. A hosted service,
generated SDK releases, distributed Redis fanout, collaborative WebSockets, administrative key
management, and remote deployment are planned or deliberately deferred. PostgreSQL remains the
production authority; the SQLite option exists only for local development and fast contract tests.

Licensed under Apache-2.0.
