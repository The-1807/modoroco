from __future__ import annotations

import argparse
import asyncio
import signal
from datetime import datetime, timezone

import structlog
from sqlalchemy import select, text

from modoroco.application.service import execute_command
from modoroco.domain import Command, DomainError
from modoroco.infrastructure.config import get_settings
from modoroco.infrastructure.database import (
    OutboxModel,
    SessionModel,
    build_engine,
    build_session_factory,
)

log = structlog.get_logger()


async def check_database() -> bool:
    settings = get_settings()
    engine = build_engine(settings)
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
        return True
    finally:
        await engine.dispose()


async def run() -> None:
    settings = get_settings()
    engine = build_engine(settings)
    sessions = build_session_factory(engine)
    stopped = asyncio.Event()
    loop = asyncio.get_running_loop()
    for sig in (signal.SIGINT, signal.SIGTERM):
        loop.add_signal_handler(sig, stopped.set)
    try:
        while not stopped.is_set():
            now = datetime.now(timezone.utc)
            async with sessions() as db:
                due = (
                    await db.scalars(
                        select(SessionModel)
                        .where(SessionModel.state == "running", SessionModel.expected_end_at <= now)
                        .with_for_update(skip_locked=True)
                        .limit(settings.worker_batch_size)
                    )
                ).all()
                for model in due:
                    try:
                        await execute_command(
                            db, model, Command.COMPLETE_PHASE, model.version, now, None
                        )
                    except DomainError as exc:
                        log.warning(
                            "due_transition_rejected", session_id=str(model.id), error=str(exc)
                        )
                outbox = (
                    await db.scalars(
                        select(OutboxModel)
                        .where(OutboxModel.state == "pending", OutboxModel.next_retry_at <= now)
                        .with_for_update(skip_locked=True)
                        .limit(settings.worker_batch_size)
                    )
                ).all()
                for record in outbox:
                    record.state = "delivered"
                    record.delivered_at = now
                await db.commit()
                if due or outbox:
                    log.info("worker_batch", transitions=len(due), outbox=len(outbox))
            try:
                await asyncio.wait_for(stopped.wait(), timeout=settings.worker_poll_seconds)
            except TimeoutError:
                continue
    finally:
        await engine.dispose()


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify worker database readiness and exit.",
    )
    args = parser.parse_args()
    if args.check:
        raise SystemExit(0 if asyncio.run(check_database()) else 1)
    asyncio.run(run())
