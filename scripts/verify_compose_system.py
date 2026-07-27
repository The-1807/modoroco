from __future__ import annotations

import json
import os
import subprocess
import time
from pathlib import Path
from typing import Any
from urllib.error import HTTPError
from urllib.request import Request, urlopen

BASE_URL = os.environ.get("MODOROCO_VERIFY_BASE_URL", "http://127.0.0.1:8000")
API_KEY = os.environ["MODOROCO_VERIFY_API_KEY"]
ARTIFACT_DIR = Path(os.environ.get("MODOROCO_ARTIFACT_DIR", "artifacts/compose"))
RESULTS: dict[str, dict[str, Any]] = {}


def request(
    method: str,
    path: str,
    *,
    body: dict[str, Any] | None = None,
    api_key: str | None = API_KEY,
    idempotency_key: str | None = None,
    expected: int = 200,
) -> tuple[int, Any, str]:
    headers = {"Accept": "application/json"}
    if api_key:
        headers["X-API-Key"] = api_key
    if idempotency_key:
        headers["Idempotency-Key"] = idempotency_key
    data = None
    if body is not None:
        data = json.dumps(body).encode()
        headers["Content-Type"] = "application/json"
    req = Request(f"{BASE_URL}{path}", data=data, headers=headers, method=method)
    try:
        with urlopen(req, timeout=5) as response:
            status = response.status
            content_type = response.headers.get("Content-Type", "")
            raw = response.read().decode()
    except HTTPError as exc:
        status = exc.code
        content_type = exc.headers.get("Content-Type", "")
        raw = exc.read().decode()
    if status != expected:
        raise AssertionError(f"{method} {path}: expected {expected}, received {status}: {raw}")
    parsed = json.loads(raw) if "json" in content_type else raw
    return status, parsed, content_type


def stage(name: str, operation) -> Any:
    started = time.monotonic()
    try:
        result = operation()
    except Exception as exc:
        RESULTS[name] = {
            "status": "failed",
            "duration_seconds": round(time.monotonic() - started, 3),
            "error": str(exc),
        }
        write_reports()
        raise
    RESULTS[name] = {
        "status": "passed",
        "duration_seconds": round(time.monotonic() - started, 3),
    }
    print(json.dumps({"stage": name, **RESULTS[name]}), flush=True)
    return result


def wait_ready(timeout: float = 45) -> None:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        try:
            request("GET", "/ready", api_key=None)
            return
        except Exception:
            time.sleep(1)
    raise TimeoutError("API readiness did not recover within bounded timeout")


def compose(*args: str) -> str:
    completed = subprocess.run(
        ["docker", "compose", *args],
        check=True,
        text=True,
        capture_output=True,
        timeout=120,
    )
    return completed.stdout


def sql(query: str) -> str:
    return compose(
        "exec",
        "-T",
        "postgres",
        "psql",
        "-U",
        "modoroco",
        "-d",
        "modoroco",
        "-Atc",
        query,
    ).strip()


def main() -> int:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    stage("api_ready", wait_ready)
    stage("liveness", lambda: request("GET", "/live", api_key=None))
    stage(
        "metrics",
        lambda: _assert_metrics(request("GET", "/metrics", api_key=None)),
    )
    stage(
        "authentication_rejection",
        lambda: (
            request("GET", "/v1/families", api_key=None, expected=401),
            request("GET", "/v1/families", api_key="invalid", expected=401),
        ),
    )

    family_payload = {"name": "Hosted verification", "description": "Ephemeral system test"}
    _, family, _ = stage(
        "family_create",
        lambda: request(
            "POST",
            "/v1/families",
            body=family_payload,
            idempotency_key="hosted-family-0001",
            expected=201,
        ),
    )
    _, replay, _ = stage(
        "family_idempotent_replay",
        lambda: request(
            "POST",
            "/v1/families",
            body=family_payload,
            idempotency_key="hosted-family-0001",
            expected=201,
        ),
    )
    assert replay == family
    stage(
        "family_idempotency_conflict",
        lambda: request(
            "POST",
            "/v1/families",
            body={"name": "Conflicting payload"},
            idempotency_key="hosted-family-0001",
            expected=409,
        ),
    )

    _, version, _ = stage(
        "family_version",
        lambda: request(
            "POST",
            f"/v1/families/{family['id']}/versions",
            body={
                "phases": [
                    {
                        "key": "focus",
                        "name": "Focus",
                        "phase_type": "focus",
                        "duration_seconds": 2,
                    }
                ]
            },
            expected=201,
        ),
    )
    _, session, _ = stage(
        "session_create",
        lambda: request(
            "POST",
            "/v1/sessions",
            body={"family_version_id": version["id"]},
            expected=201,
        ),
    )
    _, started, _ = stage(
        "session_start",
        lambda: request(
            "POST",
            f"/v1/sessions/{session['id']}/commands",
            body={"command": "start", "expected_version": 1},
            idempotency_key="hosted-session-start-0001",
        ),
    )
    assert started["state"] == "running" and started["expected_end_at"]
    stage(
        "session_idempotent_replay",
        lambda: _assert_equal(
            request(
                "POST",
                f"/v1/sessions/{session['id']}/commands",
                body={"command": "start", "expected_version": 1},
                idempotency_key="hosted-session-start-0001",
            )[1],
            started,
        ),
    )
    stage(
        "stale_version_rejection",
        lambda: request(
            "POST",
            f"/v1/sessions/{session['id']}/commands",
            body={"command": "pause", "expected_version": 1},
            idempotency_key="hosted-session-pause-0001",
            expected=409,
        ),
    )

    completed = stage(
        "automatic_transition",
        lambda: wait_session_state(session["id"], "completed", 30),
    )
    assert completed["version"] == 3
    _, events, _ = stage(
        "session_events",
        lambda: request("GET", f"/v1/sessions/{session['id']}/events"),
    )
    event_types = [event["type"] for event in events]
    assert event_types.count("phase.completed") == 1
    assert len(events) < 10

    stage(
        "persistence_evidence",
        lambda: _assert_database_evidence(session["id"]),
    )
    stage("api_restart", lambda: _restart_and_recover("api", session["id"]))
    stage("worker_restart", lambda: _restart_worker())
    stage("database_outage_recovery", _database_outage_recovery)
    stage("full_stack_restart", lambda: _full_restart(session["id"], family["id"]))
    stage("sse", lambda: _verify_sse(session["id"]))
    write_reports()
    return 0


def wait_session_state(session_id: str, state: str, timeout: float) -> dict[str, Any]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        current = request("GET", f"/v1/sessions/{session_id}")[1]
        if current["state"] == state:
            return current
        time.sleep(0.5)
    raise TimeoutError(f"session {session_id} did not reach {state}")


def _assert_metrics(response: tuple[int, Any, str]) -> None:
    _, body, content_type = response
    assert "text/plain" in content_type
    assert "modoroco_http_requests_total" in body


def _assert_equal(actual: Any, expected: Any) -> None:
    assert actual == expected


def _assert_database_evidence(session_id: str) -> None:
    assert (
        sql(f"SELECT count(*) FROM session_phase_history WHERE session_id = '{session_id}'") == "1"
    )
    assert (
        sql(
            f"SELECT count(*) FROM domain_events WHERE session_id = '{session_id}' "
            "AND event_type = 'phase.completed'"
        )
        == "1"
    )
    assert (
        sql(
            "SELECT count(*) FROM outbox WHERE payload->>'session_id' = "
            f"'{session_id}' AND event_type = 'phase.completed'"
        )
        == "1"
    )


def _restart_and_recover(service: str, session_id: str) -> None:
    before = request("GET", f"/v1/sessions/{session_id}")[1]
    compose("restart", service)
    wait_ready()
    after = request("GET", f"/v1/sessions/{session_id}")[1]
    assert after["id"] == before["id"]
    assert after["version"] == before["version"]


def _restart_worker() -> None:
    compose("restart", "worker")
    output = compose("exec", "-T", "worker", "modoroco-worker", "--check")
    assert "password" not in output.lower()


def _database_outage_recovery() -> None:
    compose("stop", "postgres")
    request("GET", "/live", api_key=None)
    try:
        request("GET", "/ready", api_key=None)
    except AssertionError:
        pass
    else:
        raise AssertionError("readiness incorrectly succeeded without PostgreSQL")
    worker = subprocess.run(
        ["docker", "compose", "exec", "-T", "worker", "modoroco-worker", "--check"],
        timeout=20,
    )
    assert worker.returncode != 0
    compose("start", "postgres")
    wait_ready()
    compose("exec", "-T", "worker", "modoroco-worker", "--check")


def _full_restart(session_id: str, family_id: str) -> None:
    volume_before = compose("config", "--volumes").strip()
    compose("stop")
    assert volume_before
    compose("start", "postgres")
    compose("run", "--rm", "migrate")
    compose("start", "api", "worker")
    wait_ready()
    request("GET", f"/v1/families/{family_id}")
    request("GET", f"/v1/sessions/{session_id}")
    assert volume_before == compose("config", "--volumes").strip()


def _verify_sse(session_id: str) -> None:
    req = Request(
        f"{BASE_URL}/v1/sessions/{session_id}/stream",
        headers={"X-API-Key": API_KEY},
    )
    with urlopen(req, timeout=5) as response:
        assert "text/event-stream" in response.headers.get("Content-Type", "")
        lines = []
        for _ in range(12):
            line = response.readline().decode()
            if not line:
                break
            lines.append(line)
            if any(item.startswith("event:") for item in lines) and any(
                item.startswith("data:") for item in lines
            ):
                break
        chunk = "".join(lines)
    assert "event:" in chunk and "data:" in chunk


def write_reports() -> None:
    report = {"base_url": BASE_URL, "stages": RESULTS}
    (ARTIFACT_DIR / "verification.json").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )
    lines = ["# Compose system verification", ""]
    for name, result in RESULTS.items():
        lines.append(f"- **{name}**: {result['status']} ({result['duration_seconds']} seconds)")
    (ARTIFACT_DIR / "verification.md").write_text(
        "\n".join(lines) + "\n",
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
