# Persistence model

The initial migration creates tenants, API clients, timer families, immutable family versions,
sessions, domain events, transactional outbox records, and idempotency records. Foreign keys and
tenant indexes support isolation. `(family_id, version)` and the full idempotency scope are unique.

Session columns expose state, version, due time, and phase index for concurrency-safe querying;
the aggregate snapshot is stored as JSON for faithful reconstruction. Events and outbox records
share a UUID and are inserted in the same SQLAlchemy transaction as state changes.

