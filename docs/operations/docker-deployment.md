# Docker deployment

The multi-stage image installs a frozen environment, runs as UID 1807, exposes only port 8000,
and includes an application liveness health check. Compose provides PostgreSQL 18, a one-shot
migration job, API, and worker on an internal backend network. Application containers are
read-only with a temporary `/tmp`.

Production operators must supply secrets externally, terminate TLS, back up PostgreSQL, monitor
outbox backlog, and run migrations as a controlled release job. No public hosted deployment is
claimed by this repository.

