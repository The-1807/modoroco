# Local development

Install Python 3.13 and `uv`, copy `.env.example` to `.env`, set a unique database password and a
high-entropy bootstrap key, then run `uv sync --locked --all-extras --all-groups`. Start infrastructure
with `docker compose up --build`; migration completion gates both API and worker startup.

Use `uv sync --locked --extra server --group dev` for server-only development or
`uv sync --locked --extra desktop --group dev` for desktop-only development. The production-style
server selection is `uv sync --locked --no-dev --extra server`.

Without Docker, set `MODOROCO_DATABASE_URL=sqlite+aiosqlite:///./modoroco.db` for local API work.
SQLite is not the deployment authority and does not validate PostgreSQL locking semantics.

Run `alembic upgrade head`, `modoroco-api`, or `modoroco-worker` independently. The native client
is launched with `modoroco`.

