from pathlib import Path

from fastapi.testclient import TestClient

from modoroco.infrastructure.config import Settings
from modoroco.interfaces.api import create_app


def test_authenticated_api_lifecycle(tmp_path: Path) -> None:
    settings = Settings(
        environment="test",
        database_url=f"sqlite+aiosqlite:///{tmp_path / 'api.db'}",
        bootstrap_api_key="development-secret",
    )
    with TestClient(create_app(settings)) as client:
        assert client.get("/live").status_code == 200
        assert client.get("/ready").json()["database"] == "available"
        assert client.get("/v1/families").status_code == 401
        headers = {"X-API-Key": "development-secret"}
        family = client.post(
            "/v1/families",
            headers=headers,
            json={"name": "Classic", "description": "Balanced focus"},
        ).json()
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
