from datetime import datetime, timedelta, timezone
from pathlib import Path
from uuid import uuid4

from sqlalchemy import func, select

from modoroco.application.service import execute_command, persist_new
from modoroco.domain import Command, Phase, PhaseType, Session
from modoroco.infrastructure.config import Settings
from modoroco.infrastructure.database import (
    Base,
    FamilyModel,
    FamilyVersionModel,
    OutboxModel,
    SessionModel,
    SessionPhaseModel,
    TenantModel,
    build_engine,
    build_session_factory,
)
from modoroco.runtime.worker import process_batch


async def test_worker_completes_due_phase_once_and_persists_history(
    tmp_path: Path,
) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'worker.db'}",
    )
    engine = build_engine(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = build_session_factory(engine)
    now = datetime.now(timezone.utc)
    tenant_id, family_id, version_id = uuid4(), uuid4(), uuid4()
    phase = Phase("focus", "Focus", PhaseType.FOCUS, 1)

    async with sessions() as db:
        db.add(TenantModel(id=tenant_id, name="Worker test", created_at=now))
        db.add(
            FamilyModel(
                id=family_id,
                tenant_id=tenant_id,
                name="Short",
                description="",
                created_at=now,
            )
        )
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
        aggregate = Session.create(tenant_id, version_id, (phase,), now)
        await persist_new(db, aggregate)
        await db.flush()
        model = await db.get(SessionModel, aggregate.session_id)
        assert model is not None
        await execute_command(db, model, Command.START, 1, now, None)
        await db.commit()

    async with sessions() as db:
        transitioned, delivered, failures = await process_batch(
            db,
            now + timedelta(seconds=2),
            50,
        )
        assert (transitioned, failures) == (1, 0)
        assert delivered >= 1
        history = await db.scalar(
            select(func.count())
            .select_from(SessionPhaseModel)
            .where(SessionPhaseModel.session_id == aggregate.session_id)
        )
        assert history == 1
        model = await db.get(SessionModel, aggregate.session_id)
        assert model is not None
        assert model.state == "completed"
        assert model.version == 3

        transitioned, _, _ = await process_batch(
            db,
            now + timedelta(seconds=3),
            50,
        )
        assert transitioned == 0
        history = await db.scalar(
            select(func.count())
            .select_from(SessionPhaseModel)
            .where(SessionPhaseModel.session_id == aggregate.session_id)
        )
        assert history == 1
    await engine.dispose()


async def test_outbox_failure_uses_bounded_retry_and_then_delivers(
    tmp_path: Path,
) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'outbox.db'}",
    )
    engine = build_engine(settings)
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
    sessions = build_session_factory(engine)
    now = datetime.now(timezone.utc)
    record_id = uuid4()

    async with sessions() as db:
        db.add(
            OutboxModel(
                id=record_id,
                event_type="verification.event",
                payload={"safe": True},
                state="pending",
                retry_count=0,
                next_retry_at=now,
                created_at=now,
            )
        )
        await db.commit()

    async def fail_delivery(record: OutboxModel) -> None:
        del record
        raise RuntimeError("controlled delivery failure")

    async with sessions() as db:
        _, delivered, failures = await process_batch(
            db,
            now,
            50,
            fail_delivery,
        )
        assert (delivered, failures) == (0, 1)
        record = await db.get(OutboxModel, record_id)
        assert record is not None
        assert record.state == "failed"
        assert record.retry_count == 1
        assert record.last_error == "controlled delivery failure"
        assert record.next_retry_at.replace(tzinfo=timezone.utc) == (now + timedelta(seconds=2))

    async with sessions() as db:
        _, delivered, failures = await process_batch(
            db,
            now + timedelta(seconds=2),
            50,
        )
        assert (delivered, failures) == (1, 0)
        record = await db.get(OutboxModel, record_id)
        assert record is not None
        assert record.state == "delivered"
        assert record.delivered_at is not None
    await engine.dispose()
