from __future__ import annotations

import asyncio
import json
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from typing import Annotated
from uuid import UUID, uuid4

from fastapi import Depends, FastAPI, Header, HTTPException, Request, Response, status
from fastapi.responses import PlainTextResponse, StreamingResponse
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field
from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from modoroco.application.service import (
    execute_command,
    get_session,
    persist_new,
    serialize_session,
)
from modoroco.domain import Command, DomainError, Phase, PhaseType, Session, VersionConflict
from modoroco.infrastructure.auth import Principal, authenticate, digest_api_key
from modoroco.infrastructure.config import Settings, get_settings
from modoroco.infrastructure.database import (
    ApiClientModel,
    Base,
    EventModel,
    FamilyModel,
    FamilyVersionModel,
    IdempotencyModel,
    TenantModel,
    build_engine,
    build_session_factory,
)

REQUESTS = Counter("modoroco_http_requests_total", "HTTP requests", ["method", "path", "status"])
LATENCY = Histogram("modoroco_http_request_duration_seconds", "HTTP request latency", ["path"])
COMMANDS = Counter("modoroco_session_commands_total", "Session commands", ["command", "result"])


class PhaseInput(BaseModel):
    key: str = Field(min_length=1, max_length=60, pattern=r"^[a-z0-9_-]+$")
    name: str = Field(min_length=1, max_length=100)
    phase_type: PhaseType
    duration_seconds: int = Field(ge=1, le=14_400)
    skippable: bool = True
    extendable: bool = True
    max_duration_seconds: int = Field(default=14_400, ge=1, le=86_400)


class FamilyCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    description: str = Field(default="", max_length=2000)


class VersionCreate(BaseModel):
    phases: list[PhaseInput] = Field(min_length=1, max_length=32)


class SessionCreate(BaseModel):
    family_version_id: UUID


class CommandInput(BaseModel):
    command: Command
    expected_version: int = Field(ge=1)
    extend_seconds: int | None = Field(default=None, ge=1, le=14_400)


def create_app(settings: Settings | None = None) -> FastAPI:
    config = settings or get_settings()
    engine = build_engine(config)
    sessions = build_session_factory(engine)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        app.state.engine = engine
        app.state.sessions = sessions
        if config.environment == "test" or config.database_url.startswith("sqlite"):
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
        await _bootstrap(config, sessions)
        yield
        await engine.dispose()

    app = FastAPI(title="Modoroco API", version="0.1.0", openapi_version="3.1.0", lifespan=lifespan)

    @app.middleware("http")
    async def observe(request: Request, call_next):
        correlation = request.headers.get("X-Correlation-ID", str(uuid4()))[:128]
        with LATENCY.labels(request.url.path).time():
            response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation
        REQUESTS.labels(request.method, request.url.path, response.status_code).inc()
        return response

    async def db_session(request: Request) -> AsyncIterator[AsyncSession]:
        async with request.app.state.sessions() as db:
            yield db

    async def principal(
        x_api_key: Annotated[str | None, Header()] = None,
        db: AsyncSession = Depends(db_session),
    ) -> Principal:
        if not x_api_key or (identity := await authenticate(db, x_api_key)) is None:
            raise HTTPException(
                status.HTTP_401_UNAUTHORIZED,
                detail={"code": "invalid_api_key", "message": "A valid API key is required"},
            )
        await db.commit()
        return identity

    @app.exception_handler(DomainError)
    async def domain_error(request: Request, exc: DomainError):
        code = getattr(exc, "code", "invalid_transition")
        payload = {
            "code": code,
            "message": str(exc),
            "correlation_id": request.headers.get("X-Correlation-ID"),
        }
        if isinstance(exc, VersionConflict):
            payload["current_version"] = exc.current_version
        return Response(
            json.dumps(payload),
            status_code=409 if isinstance(exc, VersionConflict) else 422,
            media_type="application/json",
        )

    @app.get("/live", tags=["health"])
    async def live() -> dict[str, str]:
        return {"status": "alive"}

    @app.get("/ready", tags=["health"])
    async def ready(db: AsyncSession = Depends(db_session)) -> dict[str, str]:
        await db.execute(text("SELECT 1"))
        return {"status": "ready", "database": "available"}

    @app.get("/metrics", response_class=PlainTextResponse, tags=["health"])
    async def metrics() -> Response:
        return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)

    @app.post("/v1/families", status_code=201)
    async def create_family(
        body: FamilyCreate,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        family = FamilyModel(
            id=uuid4(),
            tenant_id=identity.tenant_id,
            name=body.name,
            description=body.description,
            created_at=datetime.now(timezone.utc),
        )
        db.add(family)
        await db.commit()
        return _family(family)

    @app.get("/v1/families")
    async def list_families(
        identity: Principal = Depends(principal), db: AsyncSession = Depends(db_session)
    ):
        values = (
            await db.scalars(select(FamilyModel).where(FamilyModel.tenant_id == identity.tenant_id))
        ).all()
        return [_family(item) for item in values]

    @app.get("/v1/families/{family_id}")
    async def read_family(
        family_id: UUID,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        family = await db.scalar(
            select(FamilyModel).where(
                FamilyModel.id == family_id, FamilyModel.tenant_id == identity.tenant_id
            )
        )
        if family is None:
            raise HTTPException(
                404, detail={"code": "family_not_found", "message": "Family was not found"}
            )
        return _family(family)

    @app.post("/v1/families/{family_id}/versions", status_code=201)
    async def publish_version(
        family_id: UUID,
        body: VersionCreate,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        family = await db.scalar(
            select(FamilyModel).where(
                FamilyModel.id == family_id, FamilyModel.tenant_id == identity.tenant_id
            )
        )
        if family is None:
            raise HTTPException(404, detail="Family was not found")
        current = (
            await db.scalar(
                select(func.max(FamilyVersionModel.version)).where(
                    FamilyVersionModel.family_id == family_id
                )
            )
            or 0
        )
        phases = [item.model_dump(mode="json") for item in body.phases]
        for item in body.phases:
            Phase(**item.model_dump())
        version = FamilyVersionModel(
            id=uuid4(),
            family_id=family_id,
            tenant_id=identity.tenant_id,
            version=current + 1,
            phases=phases,
            published_at=datetime.now(timezone.utc),
        )
        db.add(version)
        await db.commit()
        return {
            "id": version.id,
            "family_id": family_id,
            "version": version.version,
            "phases": phases,
            "published_at": version.published_at,
        }

    @app.post("/v1/sessions", status_code=201)
    async def create_session(
        body: SessionCreate,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        version = await db.scalar(
            select(FamilyVersionModel).where(
                FamilyVersionModel.id == body.family_version_id,
                FamilyVersionModel.tenant_id == identity.tenant_id,
            )
        )
        if version is None:
            raise HTTPException(404, detail="Family version was not found")
        phases = tuple(
            Phase(
                key=p["key"],
                name=p["name"],
                phase_type=PhaseType(p["phase_type"]),
                duration_seconds=p["duration_seconds"],
                skippable=p["skippable"],
                extendable=p["extendable"],
                max_duration_seconds=p["max_duration_seconds"],
            )
            for p in version.phases
        )
        aggregate = Session.create(
            identity.tenant_id, version.id, phases, datetime.now(timezone.utc)
        )
        await persist_new(db, aggregate)
        await db.commit()
        return serialize_session(aggregate)

    @app.get("/v1/sessions/{session_id}")
    async def read_session(
        session_id: UUID,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        model = await get_session(db, session_id, identity.tenant_id)
        if model is None:
            raise HTTPException(404, detail="Session was not found")
        return model.data

    @app.post("/v1/sessions/{session_id}/commands")
    async def command_session(
        session_id: UUID,
        body: CommandInput,
        idempotency_key: Annotated[str, Header(min_length=8, max_length=200)],
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        operation = f"session:{session_id}:{body.command.value}"
        existing = await db.scalar(
            select(IdempotencyModel).where(
                IdempotencyModel.tenant_id == identity.tenant_id,
                IdempotencyModel.client_id == identity.client_id,
                IdempotencyModel.operation == operation,
                IdempotencyModel.key == idempotency_key,
            )
        )
        if existing:
            return existing.response
        model = await get_session(db, session_id, identity.tenant_id)
        if model is None:
            raise HTTPException(404, detail="Session was not found")
        try:
            aggregate = await execute_command(
                db,
                model,
                body.command,
                body.expected_version,
                datetime.now(timezone.utc),
                body.extend_seconds,
            )
        except DomainError:
            COMMANDS.labels(body.command.value, "rejected").inc()
            raise
        response = serialize_session(aggregate)
        db.add(
            IdempotencyModel(
                tenant_id=identity.tenant_id,
                client_id=identity.client_id,
                operation=operation,
                key=idempotency_key,
                response=response,
                created_at=datetime.now(timezone.utc),
            )
        )
        await db.commit()
        COMMANDS.labels(body.command.value, "accepted").inc()
        return response

    @app.get("/v1/sessions/{session_id}/events")
    async def session_events(
        session_id: UUID,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        if await get_session(db, session_id, identity.tenant_id) is None:
            raise HTTPException(404, detail="Session was not found")
        events = (
            await db.scalars(
                select(EventModel)
                .where(
                    EventModel.session_id == session_id, EventModel.tenant_id == identity.tenant_id
                )
                .order_by(EventModel.occurred_at)
            )
        ).all()
        return [
            {"id": e.id, "type": e.event_type, "occurred_at": e.occurred_at, "payload": e.payload}
            for e in events
        ]

    @app.get("/v1/sessions/{session_id}/stream")
    async def session_stream(
        session_id: UUID,
        identity: Principal = Depends(principal),
        db: AsyncSession = Depends(db_session),
    ):
        if await get_session(db, session_id, identity.tenant_id) is None:
            raise HTTPException(404, detail="Session was not found")

        async def generate():
            last: UUID | None = None
            while True:
                async with sessions() as stream_db:
                    query = (
                        select(EventModel)
                        .where(
                            EventModel.session_id == session_id,
                            EventModel.tenant_id == identity.tenant_id,
                        )
                        .order_by(EventModel.occurred_at)
                    )
                    values = (await stream_db.scalars(query)).all()
                    for event in values:
                        if last is None or event.id != last:
                            last = event.id
                            yield (
                                f"id: {event.id}\nevent: {event.event_type}\n"
                                f"data: {json.dumps(event.payload)}\n\n"
                            )
                await asyncio.sleep(1)

        return StreamingResponse(generate(), media_type="text/event-stream")

    return app


def _family(value: FamilyModel) -> dict:
    return {
        "id": value.id,
        "name": value.name,
        "description": value.description,
        "created_at": value.created_at,
    }


async def _bootstrap(settings: Settings, sessions) -> None:
    key = settings.bootstrap_api_key.get_secret_value() if settings.bootstrap_api_key else None
    if not key:
        return
    tenant_id, client_id = UUID(settings.bootstrap_tenant_id), UUID(settings.bootstrap_client_id)
    async with sessions() as db:
        if await db.get(TenantModel, tenant_id) is None:
            now = datetime.now(timezone.utc)
            db.add(TenantModel(id=tenant_id, name="Development", created_at=now))
            db.add(
                ApiClientModel(
                    id=client_id,
                    tenant_id=tenant_id,
                    name="Development client",
                    key_digest=digest_api_key(key),
                    active=True,
                    created_at=now,
                )
            )
            await db.commit()
