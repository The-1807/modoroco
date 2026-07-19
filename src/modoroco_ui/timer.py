"""Timestamp-driven timer domain used by the native interface."""

from __future__ import annotations

from dataclasses import dataclass, replace
from datetime import datetime, timedelta, timezone
from enum import Enum


class TimerState(str, Enum):
    READY = "ready"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETE = "complete"


@dataclass(frozen=True, slots=True)
class TimerSnapshot:
    duration: timedelta
    state: TimerState = TimerState.READY
    started_at: datetime | None = None
    expected_end_at: datetime | None = None
    paused_remaining: timedelta | None = None

    @classmethod
    def minutes(cls, value: int) -> TimerSnapshot:
        if value <= 0:
            raise ValueError("Timer duration must be positive")
        return cls(duration=timedelta(minutes=value))

    def start(self, now: datetime) -> TimerSnapshot:
        now = _utc(now)
        if self.state not in {TimerState.READY, TimerState.COMPLETE}:
            raise ValueError(f"Cannot start a {self.state.value} timer")
        return replace(
            self,
            state=TimerState.RUNNING,
            started_at=now,
            expected_end_at=now + self.duration,
            paused_remaining=None,
        )

    def pause(self, now: datetime) -> TimerSnapshot:
        if self.state is not TimerState.RUNNING:
            raise ValueError("Only a running timer can be paused")
        remaining = self.remaining(now)
        return replace(
            self,
            state=TimerState.PAUSED,
            expected_end_at=None,
            paused_remaining=remaining,
        )

    def resume(self, now: datetime) -> TimerSnapshot:
        now = _utc(now)
        if self.state is not TimerState.PAUSED or self.paused_remaining is None:
            raise ValueError("Only a paused timer can be resumed")
        return replace(
            self,
            state=TimerState.RUNNING,
            expected_end_at=now + self.paused_remaining,
            paused_remaining=None,
        )

    def reset(self) -> TimerSnapshot:
        return TimerSnapshot(duration=self.duration)

    def remaining(self, now: datetime) -> timedelta:
        if self.state is TimerState.PAUSED:
            return self.paused_remaining or timedelta()
        if self.state is TimerState.RUNNING and self.expected_end_at:
            return max(self.expected_end_at - _utc(now), timedelta())
        if self.state is TimerState.COMPLETE:
            return timedelta()
        return self.duration

    def reconcile(self, now: datetime) -> TimerSnapshot:
        if self.state is TimerState.RUNNING and self.remaining(now) == timedelta():
            return replace(self, state=TimerState.COMPLETE, expected_end_at=None)
        return self

    def with_duration(self, minutes: int) -> TimerSnapshot:
        if self.state not in {TimerState.READY, TimerState.COMPLETE}:
            raise ValueError("Duration can only change while the timer is idle")
        return TimerSnapshot.minutes(minutes)


def _utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise ValueError("Timer timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
