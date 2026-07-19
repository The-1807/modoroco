from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from modoroco.domain import Command, Phase, PhaseType, Session
from modoroco.infrastructure.database import EventModel, OutboxModel, SessionModel


def serialize_session(value: Session) -> dict[str, Any]:
    return {
        "id": str(value.session_id),
        "tenant_id": str(value.tenant_id),
        "family_version_id": str(value.family_version_id),
        "state": value.state.value,
        "version": value.version,
        "current_phase_index": value.current_phase_index,
        "current_phase": value.current_phase.key,
        "started_at": _iso(value.started_at),
        "expected_end_at": _iso(value.expected_end_at),
        "paused_at": _iso(value.paused_at),
        "total_paused_seconds": value.total_paused_seconds,
        "paused_remaining_seconds": value.paused_remaining_seconds,
        "completed_at": _iso(value.completed_at),
        "cancelled_at": _iso(value.cancelled_at),
        "created_at": _iso(value.created_at),
        "phases": [
            {
                "key": p.key,
                "name": p.name,
                "phase_type": p.phase_type.value,
                "duration_seconds": p.duration_seconds,
                "skippable": p.skippable,
                "extendable": p.extendable,
                "max_duration_seconds": p.max_duration_seconds,
            }
            for p in value.phases
        ],
    }


def hydrate_session(data: dict[str, Any], events=()) -> Session:
    from modoroco.domain.session import SessionState

    phases = tuple(
        Phase(
            p["key"],
            p["name"],
            PhaseType(p["phase_type"]),
            p["duration_seconds"],
            p["skippable"],
            p["extendable"],
            p["max_duration_seconds"],
        )
        for p in data["phases"]
    )
    return Session(
        session_id=UUID(data["id"]),
        tenant_id=UUID(data["tenant_id"]),
        family_version_id=UUID(data["family_version_id"]),
        phases=phases,
        state=SessionState(data["state"]),
        version=data["version"],
        current_phase_index=data["current_phase_index"],
        created_at=_dt(data["created_at"]),
        started_at=_dt(data["started_at"]),
        expected_end_at=_dt(data["expected_end_at"]),
        paused_at=_dt(data["paused_at"]),
        total_paused_seconds=data["total_paused_seconds"],
        paused_remaining_seconds=data["paused_remaining_seconds"],
        completed_at=_dt(data["completed_at"]),
        cancelled_at=_dt(data["cancelled_at"]),
        events=events,
    )


async def persist_new(session: AsyncSession, aggregate: Session) -> None:
    data = serialize_session(aggregate)
    session.add(
        SessionModel(
            id=aggregate.session_id,
            tenant_id=aggregate.tenant_id,
            family_version_id=aggregate.family_version_id,
            state=aggregate.state.value,
            version=aggregate.version,
            current_phase_index=aggregate.current_phase_index,
            data=data,
            expected_end_at=aggregate.expected_end_at,
            created_at=aggregate.created_at,
        )
    )
    await _persist_events(session, aggregate, 0)


async def execute_command(
    db: AsyncSession,
    model: SessionModel,
    command: Command,
    expected_version: int,
    now: datetime,
    extend_seconds: int | None,
) -> Session:
    aggregate = hydrate_session(model.data)
    changed = aggregate.execute(command, expected_version, now, extend_seconds)
    previous_events = len(aggregate.events)
    model.state = changed.state.value
    model.version = changed.version
    model.current_phase_index = changed.current_phase_index
    model.expected_end_at = changed.expected_end_at
    model.data = serialize_session(changed)
    await _persist_events(db, changed, previous_events)
    return changed


async def get_session(db: AsyncSession, session_id: UUID, tenant_id: UUID) -> SessionModel | None:
    return await db.scalar(
        select(SessionModel).where(
            SessionModel.id == session_id, SessionModel.tenant_id == tenant_id
        )
    )


async def _persist_events(db: AsyncSession, aggregate: Session, start: int) -> None:
    for event in aggregate.events[start:]:
        payload = {**event.payload, "tenant_id": str(aggregate.tenant_id)}
        db.add(
            EventModel(
                id=event.event_id,
                tenant_id=aggregate.tenant_id,
                session_id=aggregate.session_id,
                event_type=event.event_type,
                payload=payload,
                occurred_at=event.occurred_at,
            )
        )
        db.add(
            OutboxModel(
                id=event.event_id,
                event_type=event.event_type,
                payload=payload,
                state="pending",
                retry_count=0,
                next_retry_at=event.occurred_at,
                created_at=event.occurred_at,
            )
        )


def _iso(value: datetime | None) -> str | None:
    return value.isoformat() if value else None


def _dt(value: str | None) -> datetime | None:
    return datetime.fromisoformat(value) if value else None


def now_utc() -> datetime:
    return datetime.now(timezone.utc)
