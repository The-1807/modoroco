from datetime import datetime, timezone
from pathlib import Path
from secrets import token_urlsafe
from uuid import uuid4

from fastapi.testclient import TestClient

from modoroco.infrastructure.auth import digest_api_key
from modoroco.infrastructure.config import Settings
from modoroco.infrastructure.database import (
    ApiClientModel,
    TenantModel,
    build_engine,
    build_session_factory,
)
from modoroco.interfaces.api import create_app


def test_authenticated_api_lifecycle(tmp_path: Path) -> None:
    api_key = token_urlsafe(32)
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'api.db'}",
        bootstrap_api_key=api_key,
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/live").status_code == 200
        assert client.get("/ready").json()["database"] == "available"
        assert client.get("/v1/families").status_code == 401
        headers = {"X-API-Key": api_key}
        family_headers = {**headers, "Idempotency-Key": "family-create-0001"}
        family_response = client.post(
            "/v1/families",
            headers=family_headers,
            json={"name": "Classic", "description": "Balanced focus"},
        )
        family = family_response.json()
        replay = client.post(
            "/v1/families",
            headers=family_headers,
            json={"name": "Classic", "description": "Balanced focus"},
        )
        assert replay.json() == family
        assert len(client.get("/v1/families", headers=headers).json()) == 1
        conflict = client.post(
            "/v1/families",
            headers=family_headers,
            json={"name": "Different", "description": "Conflicting replay"},
        )
        assert conflict.status_code == 409
        assert conflict.json()["detail"]["code"] == "idempotency_conflict"
        version_response = client.post(
            f"/v1/families/{family['id']}/versions",
            headers=headers,
            json={
                "phases": [
                    {
                        "key": "focus",
                        "name": "Focus",
                        "phase_type": "focus",
                        "duration_seconds": 1500,
                    }
                ]
            },
        )
        assert version_response.status_code == 201, version_response.text
        version = version_response.json()
        created = client.post(
            "/v1/sessions", headers=headers, json={"family_version_id": version["id"]}
        ).json()
        command_headers = {**headers, "Idempotency-Key": "start-command-0001"}
        started = client.post(
            f"/v1/sessions/{created['id']}/commands",
            headers=command_headers,
            json={"command": "start", "expected_version": 1},
        ).json()
        assert started["state"] == "running"
        replay = client.post(
            f"/v1/sessions/{created['id']}/commands",
            headers=command_headers,
            json={"command": "start", "expected_version": 1},
        )
        assert replay.json() == started
        command_conflict = client.post(
            f"/v1/sessions/{created['id']}/commands",
            headers=command_headers,
            json={"command": "start", "expected_version": 2},
        )
        assert command_conflict.status_code == 409
        assert command_conflict.json()["detail"]["code"] == "idempotency_conflict"
        conflict = client.post(
            f"/v1/sessions/{created['id']}/commands",
            headers={**headers, "Idempotency-Key": "pause-command-0001"},
            json={"command": "pause", "expected_version": 1},
        )
        assert conflict.status_code == 409
        assert conflict.json()["current_version"] == 2
        events = client.get(f"/v1/sessions/{created['id']}/events", headers=headers).json()
        assert [event["type"] for event in events] == ["session.created", "session.started"]
        assert client.get("/metrics").status_code == 200


def test_tenant_cannot_discover_or_mutate_another_tenants_resources(tmp_path: Path) -> None:
    import asyncio

    tenant_a_key = token_urlsafe(32)
    tenant_b_key = token_urlsafe(32)
    database_url = f"sqlite+aiosqlite:///{tmp_path / 'tenants.db'}"
    settings = Settings(
        environment="test",
        database_url=database_url,
        bootstrap_api_key=tenant_a_key,
    )
    with TestClient(create_app(settings)) as client:
        tenant_a = {"X-API-Key": tenant_a_key}
        family = client.post(
            "/v1/families",
            headers={**tenant_a, "Idempotency-Key": "tenant-a-family"},
            json={"name": "Private family"},
        ).json()

        async def create_tenant_b() -> None:
            engine = build_engine(settings)
            sessions = build_session_factory(engine)
            async with sessions() as db:
                tenant_id = uuid4()
                db.add(
                    TenantModel(
                        id=tenant_id,
                        name="Tenant B",
                        created_at=datetime.now(timezone.utc),
                    )
                )
                db.add(
                    ApiClientModel(
                        id=uuid4(),
                        tenant_id=tenant_id,
                        name="Tenant B client",
                        key_digest=digest_api_key(tenant_b_key),
                        active=True,
                        created_at=datetime.now(timezone.utc),
                    )
                )
                await db.commit()
            await engine.dispose()

        asyncio.run(create_tenant_b())
        tenant_b = {"X-API-Key": tenant_b_key}
        assert client.get("/v1/families", headers=tenant_b).json() == []
        assert client.get(f"/v1/families/{family['id']}", headers=tenant_b).status_code == 404
        assert (
            client.post(
                f"/v1/families/{family['id']}/versions",
                headers=tenant_b,
                json={
                    "phases": [
                        {
                            "key": "focus",
                            "name": "Focus",
                            "phase_type": "focus",
                            "duration_seconds": 60,
                        }
                    ]
                },
            ).status_code
            == 404
        )
