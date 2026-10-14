from dataclasses import dataclass, replace
from datetime import date, datetime, time, timedelta
from typing import Protocol

from src.domain.entities import SessionStatus, StudyPlan, StudySession


class SchedulePolicy(Protocol):
    def distribute(self, plan: StudyPlan, sessions: list[StudySession], today: date) -> list[StudySession]:
        """Return updated planned sessions without mutating the inputs."""
        ...


@dataclass(frozen=True)
class WeeklySchedulePolicy:
    day_offsets: tuple[int, ...] = (0, 2, 5)
    starts_at: time = time(hour=18)
    minimum_minutes: int = 20
    maximum_minutes: int = 180

    def __post_init__(self) -> None:
        if not self.day_offsets or any(day < 0 or day > 6 for day in self.day_offsets):
            raise ValueError("day_offsets must contain offsets from 0 to 6")
        if len(set(self.day_offsets)) != len(self.day_offsets):
            raise ValueError("day_offsets must be unique")
        if self.minimum_minutes <= 0 or self.maximum_minutes < self.minimum_minutes:
            raise ValueError("invalid session duration limits")

    def distribute(self, plan: StudyPlan, sessions: list[StudySession], today: date) -> list[StudySession]:
        planned = sorted(
            (item for item in sessions if item.status == SessionStatus.PLANNED),
            key=lambda item: item.scheduled_for,
        )
        base = max(today, plan.start_date)
        duration = min(
            self.maximum_minutes, max(self.minimum_minutes, plan.weekly_minutes // len(self.day_offsets))
        )
        return [
            replace(
                session,
                scheduled_for=datetime.combine(
                    base
                    + timedelta(
                        days=(index // len(self.day_offsets)) * 7
                        + self.day_offsets[index % len(self.day_offsets)]
                    ),
                    self.starts_at,
                ),
                duration_minutes=duration,
            )
            for index, session in enumerate(planned)
        ]
