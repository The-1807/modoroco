from datetime import datetime, timedelta, timezone
from uuid import uuid4

import pytest

from modoroco.domain import (
    Command,
    DomainError,
    Phase,
    PhaseType,
    Session,
    SessionState,
    VersionConflict,
)

NOW = datetime(2026, 7, 19, 12, tzinfo=timezone.utc)


def session() -> Session:
    phases = (
        Phase("focus", "Focus", PhaseType.FOCUS, 1500),
        Phase("break", "Restore", PhaseType.SHORT_BREAK, 300),
    )
    return Session.create(uuid4(), uuid4(), phases, NOW)


def test_complete_lifecycle_and_versioning() -> None:
    value = session()
    value = value.execute(Command.START, 1, NOW)
    assert value.state is SessionState.RUNNING
    assert value.expected_end_at == NOW + timedelta(seconds=1500)
    value = value.execute(Command.PAUSE, 2, NOW + timedelta(seconds=300))
    assert value.remaining_seconds(NOW + timedelta(days=1)) == 1200
    value = value.execute(Command.RESUME, 3, NOW + timedelta(seconds=600))
    assert value.total_paused_seconds == 300
    value = value.execute(Command.EXTEND_PHASE, 4, NOW + timedelta(seconds=700), 60)
    value = value.execute(Command.SKIP_PHASE, 5, NOW + timedelta(seconds=800))
    assert value.current_phase_index == 1
    value = value.execute(Command.COMPLETE_PHASE, 6, NOW + timedelta(seconds=900))
    assert value.state is SessionState.COMPLETED
    assert value.version == 7


def test_stale_version_is_rejected() -> None:
    value = session().execute(Command.START, 1, NOW)
    with pytest.raises(VersionConflict) as error:
        value.execute(Command.PAUSE, 1, NOW)
    assert error.value.current_version == 2


def test_terminal_session_requires_explicit_restart() -> None:
    value = session().execute(Command.CANCEL, 1, NOW)
    with pytest.raises(DomainError):
        value.execute(Command.START, 2, NOW)
    restarted = value.execute(Command.RESTART, 2, NOW)
    assert restarted.state is SessionState.CREATED
