# Database migrations

Run `alembic upgrade head` before new application processes. Review generated revisions against
the SQLAlchemy metadata and exercise upgrade and downgrade on disposable PostgreSQL instances.
Never edit an applied revision; add a forward corrective migration. Back up authoritative data
before destructive schema changes.

