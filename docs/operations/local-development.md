# Local development

Install Python 3.13 and `uv`, copy `.env.example` to `.env`, set a unique database password and a
high-entropy bootstrap key, then run `uv sync --locked --all-extras --dev`. Start infrastructure
with `docker compose up --build`; migration completion gates both API and worker startup.

Without Docker, set `MODOROCO_DATABASE_URL=sqlite+aiosqlite:///./modoroco.db` for local API work.
SQLite is not the deployment authority and does not validate PostgreSQL locking semantics.

Run `alembic upgrade head`, `modoroco-api`, or `modoroco-worker` independently. The native client
is launched with `modoroco`.

