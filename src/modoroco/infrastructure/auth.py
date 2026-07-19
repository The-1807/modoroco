from __future__ import annotations

import hashlib
import hmac
from dataclasses import dataclass
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from .database import ApiClientModel


@dataclass(frozen=True, slots=True)
class Principal:
    tenant_id: UUID
    client_id: UUID


def digest_api_key(raw_key: str) -> str:
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()


async def authenticate(session: AsyncSession, raw_key: str) -> Principal | None:
    digest = digest_api_key(raw_key)
    client = await session.scalar(select(ApiClientModel).where(ApiClientModel.key_digest == digest))
    if client is None or not client.active or not hmac.compare_digest(client.key_digest, digest):
        return None
    client.last_used_at = datetime.now(timezone.utc)
    return Principal(client.tenant_id, client.id)
