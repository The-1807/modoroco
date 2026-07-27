import asyncio
import os
from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest
from sqlalchemy import func, inspect, select

from modoroco.application.service import execute_command, persist_new
from modoroco.domain import Command, Phase, PhaseType, Session
from modoroco.infrastructure.config import Settings
from modoroco.infrastructure.database import (
    FamilyModel,
    FamilyVersionModel,
    SessionModel,
    SessionPhaseModel,
    TenantModel,
    build_engine,
    build_session_factory,
)
from modoroco.runtime.worker import process_batch

DATABASE_URL = os.environ.get("MODOROCO_TEST_DATABASE_URL")
pytestmark = pytest.mark.skipif(
    not DATABASE_URL,
    reason="requires isolated real PostgreSQL via MODOROCO_TEST_DATABASE_URL",
)


async def test_postgresql_schema_and_concurrent_worker_claims() -> None:
    assert DATABASE_URL is not None
    settings = Settings(environment="test", database_url=DATABASE_URL)
    engine = build_engine(settings)
    assert engine.dialect.name == "postgresql"

    async with engine.connect() as connection:
        schema = await connection.run_sync(_schema_evidence)
    assert "session_phase_history" in schema["tables"]
    assert "idempotency_records" in schema["tables"]
    assert "uq_idempotency_scope" in schema["unique_constraints"]
    assert "uq_session_phase_history_version" in schema["unique_constraints"]

    sessions = build_session_factory(engine)
    now = datetime.now(timezone.utc)
    tenant_id, family_id, version_id = uuid4(), uuid4(), uuid4()
    phase = Phase("focus", "Focus", PhaseType.FOCUS, 1)
    session_ids = []
    async with sessions() as db:
        db.add(TenantModel(id=tenant_id, name="PostgreSQL test", created_at=now))
        await db.flush()
        db.add(
            FamilyModel(
                id=family_id,
                tenant_id=tenant_id,
                name="Concurrent",
                description="",
                created_at=now,
            )
        )
        await db.flush()
        db.add(
            FamilyVersionModel(
                id=version_id,
                family_id=family_id,
                tenant_id=tenant_id,
                version=1,
                phases=[],
                published_at=now,
            )
        )
        await db.flush()
        for _ in range(6):
            aggregate = Session.create(tenant_id, version_id, (phase,), now)
            session_ids.append(aggregate.session_id)
            await persist_new(db, aggregate)
            await db.flush()
            model = await db.get(SessionModel, aggregate.session_id)
            assert model is not None
            await execute_command(db, model, Command.START, 1, now, None)
        await db.commit()

    async def worker() -> int:
        async with sessions() as db:
            transitions, _, failures = await process_batch(
                db,
                now + timedelta(seconds=2),
                3,
            )
            assert failures == 0
            return transitions

    claimed = await asyncio.gather(worker(), worker())
    assert sum(claimed) == 6
    async with sessions() as db:
        histories = await db.scalar(
            select(func.count())
            .select_from(SessionPhaseModel)
            .where(SessionPhaseModel.session_id.in_(session_ids))
        )
        assert histories == 6
        completed = await db.scalar(
            select(func.count())
            .select_from(SessionModel)
            .where(
                SessionModel.id.in_(session_ids),
                SessionModel.state == "completed",
                SessionModel.version == 3,
            )
        )
        assert completed == 6
    await engine.dispose()


def _schema_evidence(connection) -> dict[str, set[str]]:
    inspector = inspect(connection)
    unique_constraints: set[str] = set()
    for table in inspector.get_table_names():
        unique_constraints.update(
            constraint["name"]
            for constraint in inspector.get_unique_constraints(table)
            if constraint["name"]
        )
    return {
        "tables": set(inspector.get_table_names()),
        "unique_constraints": unique_constraints,
    }
