from datetime import date, datetime
from typing import Protocol

from src.domain.entities import (
    AnswerEvaluation,
    Assignment,
    Attempt,
    Course,
    Goal,
    Lesson,
    StudyPlan,
    StudySession,
)


class Clock(Protocol):
    def today(self) -> date: ...

    def now(self) -> datetime: ...


class CatalogReader(Protocol):
    """Return detached entities; missing IDs return None and empty filters return no rows.

    Courses are ordered by title, lessons by (course_id, position). get_courses
    preserves requested order and skips missing IDs. Search is case insensitive.
    """

    async def list_courses(self, *, level: str | None = None, skill: str | None = None) -> list[Course]: ...

    async def search_courses(self, query: str) -> list[Course]: ...

    async def get_course(self, course_id: str) -> Course | None: ...

    async def get_courses(self, course_ids: list[str]) -> list[Course]: ...

    async def count_lessons_by_course(self, course_ids: list[str]) -> dict[str, int]: ...

    async def get_lesson(self, lesson_id: str) -> Lesson | None: ...

    async def list_lessons(self, course_ids: list[str] | None = None) -> list[Lesson]: ...


class PlanReader(Protocol):
    async def get_plan(self, plan_id: str) -> StudyPlan | None: ...

    async def list_plans(self) -> list[StudyPlan]:
        """Return plans in creation order."""
        ...


class PlanRepository(PlanReader, Protocol):
    """Writes persist before returning; failed writes leave stored values unchanged."""

    async def create_plan(
        self, *, name: str, weekly_minutes: int, start_date: date, course_ids: list[str]
    ) -> StudyPlan: ...

    async def update_plan_workload(self, plan_id: str, weekly_minutes: int) -> StudyPlan:
        """Raise NotFoundError for an unknown plan."""
        ...

    async def add_goal(self, *, plan_id: str, title: str, target_date: date, target_minutes: int) -> Goal: ...

    async def delete_plan(self, plan_id: str) -> None:
        """Atomically delete the plan, its goals, and all of its sessions."""
        ...

    async def delete_goal(self, plan_id: str, goal_id: str) -> None:
        """Delete a goal belonging to the plan; unknown IDs raise NotFoundError."""
        ...

    async def remove_course(self, plan_id: str, course_id: str, lesson_ids: list[str]) -> StudyPlan:
        """Atomically remove a course and its planned sessions from the plan."""
        ...


class SessionReader(Protocol):
    """Return detached sessions in chronological order, using naive UTC timestamps."""

    async def list_sessions(
        self, *, from_date: date | None = None, to_date: date | None = None
    ) -> list[StudySession]: ...

    async def list_plan_sessions(self, plan_id: str) -> list[StudySession]: ...

    async def get_session(self, session_id: str) -> StudySession | None: ...


class SessionRepository(SessionReader, Protocol):
    async def create_session(
        self,
        *,
        plan_id: str,
        lesson_id: str,
        scheduled_for: datetime,
        duration_minutes: int,
    ) -> StudySession: ...

    async def save_session(self, session: StudySession) -> StudySession:
        """Persist the supplied values; raise NotFoundError for an unknown session."""
        ...

    async def save_sessions(self, sessions: list[StudySession]) -> None:
        """Persist all supplied values atomically; unknown IDs raise NotFoundError."""
        ...

    async def delete_session(self, session_id: str) -> None:
        """Delete a planned session; reject other states and unknown IDs."""
        ...


class PracticeReader(Protocol):
    async def get_assignment(self, assignment_id: str) -> Assignment | None: ...

    async def list_assignments(self) -> list[Assignment]: ...

    async def list_attempts(self, assignment_id: str | None = None) -> list[Attempt]:
        """Return attempts in creation order, optionally filtered by assignment."""
        ...

    async def answer_for(self, assignment_id: str) -> str | None: ...


class PracticeRepository(PracticeReader, Protocol):
    async def mark_hint_requested(self, assignment_id: str) -> None:
        """Persist a hint marker; unknown assignments raise NotFoundError."""
        ...

    async def clear_hint_marker(self, assignment_id: str) -> None:
        """Clear a hint marker; unknown assignments raise NotFoundError."""
        ...

    async def record_attempt(
        self, *, assignment_id: str, answer: str, evaluation: AnswerEvaluation
    ) -> Attempt:
        """Atomically consume the hint marker and persist the evaluated attempt.

        Select evaluation.score or evaluation.hinted_score from the stored marker.
        Failure must preserve the marker and previous attempts. Unknown assignments
        raise NotFoundError. The caller never manages a storage transaction.
        """
        ...
