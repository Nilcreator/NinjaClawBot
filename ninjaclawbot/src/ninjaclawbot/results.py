"""Structured execution results returned by ninjaclawbot."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from enum import StrEnum
from typing import Any


class ActionStatus(StrEnum):
    """Normalized completion states for robot actions."""

    SUCCESS = "success"
    FAILED = "failed"
    PARTIAL = "partial"
    REJECTED = "rejected"


@dataclass(slots=True)
class ActionResult:
    """Typed execution result for robot actions."""

    status: ActionStatus
    action: str
    started_at: datetime
    ended_at: datetime
    devices_used: list[str] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)
    error_code: str | None = None
    error_message: str | None = None
    rollback_hint: str | None = None
    request_id: str | None = None

    @property
    def duration_ms(self) -> int:
        """Return execution duration in whole milliseconds."""

        return max(0, int((self.ended_at - self.started_at).total_seconds() * 1000))

    @classmethod
    def success(
        cls,
        *,
        action: str,
        devices_used: list[str] | None = None,
        data: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        request_id: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
    ) -> "ActionResult":
        """Build a successful action result."""

        start = started_at or datetime.now(UTC)
        end = ended_at or datetime.now(UTC)
        return cls(
            status=ActionStatus.SUCCESS,
            action=action,
            started_at=start,
            ended_at=end,
            devices_used=devices_used or [],
            data=data or {},
            warnings=warnings or [],
            request_id=request_id,
        )

    @classmethod
    def failure(
        cls,
        *,
        action: str,
        error_code: str,
        error_message: str,
        rollback_hint: str | None = None,
        devices_used: list[str] | None = None,
        data: dict[str, Any] | None = None,
        warnings: list[str] | None = None,
        request_id: str | None = None,
        started_at: datetime | None = None,
        ended_at: datetime | None = None,
        status: ActionStatus = ActionStatus.FAILED,
    ) -> "ActionResult":
        """Build a failed or rejected action result."""

        start = started_at or datetime.now(UTC)
        end = ended_at or datetime.now(UTC)
        return cls(
            status=status,
            action=action,
            started_at=start,
            ended_at=end,
            devices_used=devices_used or [],
            data=data or {},
            warnings=warnings or [],
            error_code=error_code,
            error_message=error_message,
            rollback_hint=rollback_hint,
            request_id=request_id,
        )

    def to_dict(self) -> dict[str, Any]:
        """Serialize the result for transport back to an external caller."""

        return {
            "status": self.status.value,
            "action": self.action,
            "request_id": self.request_id,
            "started_at": self.started_at.isoformat(),
            "ended_at": self.ended_at.isoformat(),
            "duration_ms": self.duration_ms,
            "devices_used": list(self.devices_used),
            "data": dict(self.data),
            "warnings": list(self.warnings),
            "error_code": self.error_code,
            "error_message": self.error_message,
            "rollback_hint": self.rollback_hint,
        }
