from datetime import datetime, timedelta, timezone

import pytest

from modoroco_ui.timer import TimerSnapshot, TimerState

NOW = datetime(2026, 7, 19, 12, tzinfo=timezone.utc)


def test_running_timer_uses_authoritative_timestamp() -> None:
    timer = TimerSnapshot.minutes(25).start(NOW)
    assert timer.expected_end_at == NOW + timedelta(minutes=25)
    assert timer.remaining(NOW + timedelta(minutes=3)) == timedelta(minutes=22)


def test_pause_and_resume_preserve_remaining_time() -> None:
    timer = TimerSnapshot.minutes(25).start(NOW)
    timer = timer.pause(NOW + timedelta(minutes=5))
    assert timer.remaining(NOW + timedelta(hours=2)) == timedelta(minutes=20)
    timer = timer.resume(NOW + timedelta(hours=2))
    assert timer.expected_end_at == NOW + timedelta(hours=2, minutes=20)


def test_reconcile_completes_elapsed_timer() -> None:
    timer = TimerSnapshot.minutes(1).start(NOW)
    timer = timer.reconcile(NOW + timedelta(minutes=2))
    assert timer.state is TimerState.COMPLETE
    assert timer.remaining(NOW) == timedelta()


def test_naive_timestamp_is_rejected() -> None:
    with pytest.raises(ValueError, match="timezone-aware"):
        TimerSnapshot.minutes(25).start(datetime(2026, 7, 19, 12))


@pytest.mark.parametrize("minutes", [0, -1])
def test_invalid_duration_is_rejected(minutes: int) -> None:
    with pytest.raises(ValueError, match="positive"):
        TimerSnapshot.minutes(minutes)


def test_invalid_state_transitions_are_rejected() -> None:
    timer = TimerSnapshot.minutes(25)
    with pytest.raises(ValueError, match="running"):
        timer.pause(NOW)
    with pytest.raises(ValueError, match="paused"):
        timer.resume(NOW)
