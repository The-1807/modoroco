"""Pure timer-session aggregate and state transitions."""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from datetime import datetime, timedelta, timezone
from enum import Enum
from typing import Any
from uuid import UUID, uuid4


class DomainError(ValueError):
    code = "invalid_transition"


class VersionConflict(DomainError):
    code = "version_conflict"

    def __init__(self, current_version: int) -> None:
        super().__init__(f"Expected session version does not match {current_version}")
        self.current_version = current_version


class SessionState(str, Enum):
    CREATED = "created"
    RUNNING = "running"
    PAUSED = "paused"
    COMPLETED = "completed"
    CANCELLED = "cancelled"
    EXPIRED = "expired"


class PhaseType(str, Enum):
    FOCUS = "focus"
    SHORT_BREAK = "short_break"
    LONG_BREAK = "long_break"
    CUSTOM = "custom"


class Command(str, Enum):
    START = "start"
    PAUSE = "pause"
    RESUME = "resume"
    SKIP_PHASE = "skip_phase"
    EXTEND_PHASE = "extend_phase"
    COMPLETE_PHASE = "complete_phase"
    CANCEL = "cancel"
    RESTART = "restart"


@dataclass(frozen=True, slots=True)
class Phase:
    key: str
    name: str
    phase_type: PhaseType
    duration_seconds: int
    skippable: bool = True
    extendable: bool = True
    max_duration_seconds: int = 14_400

    def __post_init__(self) -> None:
        if not 1 <= self.duration_seconds <= self.max_duration_seconds:
            raise DomainError("Phase duration is outside its permitted bounds")


@dataclass(frozen=True, slots=True)
class DomainEvent:
    event_type: str
    occurred_at: datetime
    payload: dict[str, Any]
    event_id: UUID = field(default_factory=uuid4)


@dataclass(frozen=True, slots=True)
class Session:
    session_id: UUID
    tenant_id: UUID
    family_version_id: UUID
    phases: tuple[Phase, ...]
    state: SessionState
    version: int
    current_phase_index: int
    created_at: datetime
    started_at: datetime | None = None
    expected_end_at: datetime | None = None
    paused_at: datetime | None = None
    total_paused_seconds: int = 0
    paused_remaining_seconds: int | None = None
    completed_at: datetime | None = None
    cancelled_at: datetime | None = None
    events: tuple[DomainEvent, ...] = ()

    @classmethod
    def create(
        cls, tenant_id: UUID, family_version_id: UUID, phases: tuple[Phase, ...], now: datetime
    ) -> Session:
        if not phases:
            raise DomainError("A session requires at least one phase")
        now = aware_utc(now)
        session_id = uuid4()
        event = DomainEvent("session.created", now, {"session_id": str(session_id)})
        return cls(
            session_id,
            tenant_id,
            family_version_id,
            phases,
            SessionState.CREATED,
            1,
            0,
            now,
            events=(event,),
        )

    @property
    def current_phase(self) -> Phase:
        return self.phases[self.current_phase_index]

    def remaining_seconds(self, now: datetime) -> int:
        if self.state is SessionState.PAUSED:
            return self.paused_remaining_seconds or 0
        if self.state is SessionState.RUNNING and self.expected_end_at:
            return max(0, int((self.expected_end_at - aware_utc(now)).total_seconds()))
        return self.current_phase.duration_seconds if self.state is SessionState.CREATED else 0

    def execute(
        self,
        command: Command,
        expected_version: int,
        now: datetime,
        extend_seconds: int | None = None,
    ) -> Session:
        if expected_version != self.version:
            raise VersionConflict(self.version)
        now = aware_utc(now)
        if command is Command.START:
            return self._start(now)
        if command is Command.PAUSE:
            return self._pause(now)
        if command is Command.RESUME:
            return self._resume(now)
        if command in {Command.SKIP_PHASE, Command.COMPLETE_PHASE}:
            return self._advance(now, command is Command.SKIP_PHASE)
        if command is Command.EXTEND_PHASE:
            return self._extend(now, extend_seconds)
        if command is Command.CANCEL:
            return self._cancel(now)
        if command is Command.RESTART:
            return self._restart(now)
        raise DomainError("Unsupported command")

    def _start(self, now: datetime) -> Session:
        self._require(SessionState.CREATED)
        return self._changed(
            "session.started",
            now,
            state=SessionState.RUNNING,
            started_at=now,
            expected_end_at=now + timedelta(seconds=self.current_phase.duration_seconds),
        )

    def _pause(self, now: datetime) -> Session:
        self._require(SessionState.RUNNING)
        return self._changed(
            "session.paused",
            now,
            state=SessionState.PAUSED,
            paused_at=now,
            paused_remaining_seconds=self.remaining_seconds(now),
            expected_end_at=None,
        )

    def _resume(self, now: datetime) -> Session:
        self._require(SessionState.PAUSED)
        remaining = self.paused_remaining_seconds or 0
        paused_for = int((now - (self.paused_at or now)).total_seconds())
        return self._changed(
            "session.resumed",
            now,
            state=SessionState.RUNNING,
            paused_at=None,
            paused_remaining_seconds=None,
            total_paused_seconds=self.total_paused_seconds + max(0, paused_for),
            expected_end_at=now + timedelta(seconds=remaining),
        )

    def _advance(self, now: datetime, skipped: bool) -> Session:
        if self.state not in {SessionState.RUNNING, SessionState.PAUSED}:
            raise DomainError("Only an active session can advance phases")
        if skipped and not self.current_phase.skippable:
            raise DomainError("Current phase cannot be skipped")
        event = "phase.skipped" if skipped else "phase.completed"
        if self.current_phase_index + 1 >= len(self.phases):
            return self._changed(
                event,
                now,
                state=SessionState.COMPLETED,
                completed_at=now,
                expected_end_at=None,
                paused_at=None,
                paused_remaining_seconds=None,
            )
        index = self.current_phase_index + 1
        return self._changed(
            event,
            now,
            current_phase_index=index,
            state=SessionState.RUNNING,
            expected_end_at=now + timedelta(seconds=self.phases[index].duration_seconds),
            paused_at=None,
            paused_remaining_seconds=None,
        )

    def _extend(self, now: datetime, seconds: int | None) -> Session:
        if self.state not in {SessionState.RUNNING, SessionState.PAUSED}:
            raise DomainError("Only an active session can be extended")
        if not self.current_phase.extendable or seconds is None or seconds <= 0:
            raise DomainError("A positive permitted extension is required")
        remaining = self.remaining_seconds(now)
        if remaining + seconds > self.current_phase.max_duration_seconds:
            raise DomainError("Extension exceeds the phase maximum")
        if self.state is SessionState.PAUSED:
            return self._changed(
                "phase.extended", now, paused_remaining_seconds=remaining + seconds
            )
        return self._changed(
            "phase.extended",
            now,
            expected_end_at=(self.expected_end_at or now) + timedelta(seconds=seconds),
        )

    def _cancel(self, now: datetime) -> Session:
        if self.state in {SessionState.COMPLETED, SessionState.CANCELLED}:
            raise DomainError("A terminal session cannot be cancelled")
        return self._changed(
            "session.cancelled",
            now,
            state=SessionState.CANCELLED,
            cancelled_at=now,
            expected_end_at=None,
            paused_at=None,
        )

    def _restart(self, now: datetime) -> Session:
        if self.state not in {SessionState.COMPLETED, SessionState.CANCELLED}:
            raise DomainError("Only a terminal session can be restarted")
        return self._changed(
            "session.restarted",
            now,
            state=SessionState.CREATED,
            current_phase_index=0,
            started_at=None,
            expected_end_at=None,
            paused_at=None,
            completed_at=None,
            cancelled_at=None,
        )

    def _changed(self, event_type: str, now: datetime, **changes: Any) -> Session:
        event = DomainEvent(event_type, now, {"session_id": str(self.session_id)})
        return replace(self, version=self.version + 1, events=self.events + (event,), **changes)

    def _require(self, state: SessionState) -> None:
        if self.state is not state:
            raise DomainError(
                f"Command requires {state.value} state; session is {self.state.value}"
            )


def aware_utc(value: datetime) -> datetime:
    if value.tzinfo is None or value.utcoffset() is None:
        raise DomainError("Timestamps must be timezone-aware")
    return value.astimezone(timezone.utc)
