# Docker deployment

The multi-stage image installs the frozen `server` dependency extra, runs as UID 1807, exposes only port 8000,
and includes an application liveness health check. Compose provides PostgreSQL 18, a one-shot
migration job, API, and worker on an internal backend network. Application containers are
read-only with a temporary `/tmp`.

API and worker share this one image. Desktop-only PySide6, shiboken6, Qt libraries, test runners,
coverage tools, linters, and type checkers are excluded. Migrations and their configuration remain
in the runtime image.

Production operators must supply secrets externally, terminate TLS, back up PostgreSQL, monitor
outbox backlog, and run migrations as a controlled release job. No public hosted deployment is
claimed by this repository.

