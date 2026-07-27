# Runtime dependency model

Modoroco remains one Python project and one shared domain architecture. Dependency selection is
based on runtime responsibility:

- The base project is the core runtime. Its domain code uses the Python standard library and has
  no third-party dependency.
- The `server` extra contains Alembic, aiosqlite for the supported local fallback, asyncpg,
  FastAPI, Prometheus Client, pydantic-settings, SQLAlchemy, structlog, and Uvicorn.
- The `desktop` extra contains PySide6 and its transitive Qt/shiboken runtime.
- The PEP 735 `dev` group contains pytest, pytest-asyncio, pytest-cov, HTTPX, Hypothesis, Pyright,
  and Ruff.

The server extra owns persistence, HTTP, authentication, metrics, SSE, configuration, and worker
execution. The desktop extra owns only Qt presentation. Desktop modules may consume shared
domain behavior; server and domain modules cannot import the desktop package or PySide6.

## Locked installation commands

```text
uv sync --locked --extra server --group dev
uv sync --locked --extra desktop --group dev
uv sync --locked --all-extras --all-groups
uv sync --locked --no-dev --extra server
```

The Docker builder uses the final command with `--no-editable`. CI creates real server-only and
desktop-only environments and inspects installed distributions. The server gate rejects Qt and
development distributions; the desktop gate launches a Qt window using the offscreen platform.

## Direct dependency audit

| Dependency | Classification | Production consumer | Native/binary impact |
| --- | --- | --- | --- |
| Alembic | Server | Migrations | Low |
| aiosqlite | Server/local development | Supported SQLite fallback | Native extension, small |
| asyncpg | Server | PostgreSQL driver | Native extension |
| FastAPI | Server | HTTP API | Low |
| prometheus-client | Server | Metrics | Low |
| pydantic-settings | Server | Runtime configuration | Includes transitive pydantic-core |
| SQLAlchemy asyncio | Server | Persistence and unit of work | Includes greenlet |
| structlog | Server | Structured logging | Low |
| Uvicorn standard | Server | ASGI runtime | Includes uvloop/httptools on Linux |
| PySide6 | Desktop | Native UI | Very large Qt binary wheels |
| pytest/pytest-asyncio/pytest-cov | Development/test | Test execution and coverage | Not shipped |
| HTTPX | Development/test | FastAPI test client | Not shipped |
| Hypothesis | Development/test | Property testing | Not shipped |
| Pyright/Ruff | Development | Static analysis and linting | Not shipped |

The baseline hosted image was 853 MB at
`sha256:ca2d6b33fbe4180ff218a3adc95dab9bf5d4b12b8603c65634637eb97b62e43c`.
The optimized hosted image is 184 MB (`183,571,712` bytes) at
`sha256:e0976a9a2bf4dff8ca8ca95d48bfc296217b58a086aa426f5e72959ccf4ac2fe`.
That is a 669 MB reduction, or 78.48% relative to the recorded decimal-display baseline.

The largest remaining layers are the 74.8 MB Debian base, the 62.8 MB server virtual environment,
the 36.7 MB Python runtime layer, and 9.23 MB of base operating-system packages. Further material
reduction would require a base-image or runtime-distribution tradeoff rather than dependency
classification alone. Hosted package inventory confirms that PySide6, shiboken6, Qt, pytest,
Hypothesis, Ruff, Pyright, and coverage are absent. The full verification run is
<https://github.com/The-1807/modoroco/actions/runs/30307546243>.

The focused workflow now scans the locally built production image with SHA-pinned Anchore Grype.
The existing publish workflow continues producing provenance and SBOM attestations. `LICENSE` and
`NOTICE` are copied into the runtime image, and its Apache-2.0 OCI license label remains present.
