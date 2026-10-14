from dataclasses import replace
from datetime import date, datetime

from src.application.ports import CatalogReader, Clock, PlanReader, SessionRepository
from src.application.schemas import (
    SessionCalendar,
    SessionView,
)
from src.application.services.lookups import (
    require_lesson,
    require_plan,
    require_session,
)
from src.domain.entities import (
    SessionStatus,
    StudySession,
)
from src.domain.exceptions import ConflictError, InvalidStateError, ValidationError


class SessionService:
    def __init__(
        self, sessions: SessionRepository, plans: PlanReader, catalog: CatalogReader, clock: Clock
    ) -> None:
        self._sessions = sessions
        self._plans = plans
        self._catalog = catalog
        self._clock = clock

    async def calendar(self, from_date: date, to_date: date) -> SessionCalendar:
        if to_date < from_date:
            raise ValidationError("Конечная дата должна быть не раньше начальной")
        sessions = await self._sessions.list_sessions(from_date=from_date, to_date=to_date)
        items = [await self._session_view(item) for item in sessions]
        return SessionCalendar(items=items, total=len(items), from_date=from_date, to_date=to_date)

    async def create_session(
        self,
        *,
        plan_id: str,
        lesson_id: str,
        scheduled_for: datetime,
        duration_minutes: int,
    ) -> SessionView:
        plan = await require_plan(self._plans, plan_id)
        lesson = await require_lesson(self._catalog, lesson_id)
        if lesson.course_id not in plan.course_ids:
            raise ConflictError("Урок не относится к курсу из этого учебного плана")
        session = await self._sessions.create_session(
            plan_id=plan_id,
            lesson_id=lesson_id,
            scheduled_for=scheduled_for,
            duration_minutes=duration_minutes,
        )
        return await self._session_view(session)

    async def start_session(self, session_id: str) -> SessionView:
        session = await require_session(self._sessions, session_id)
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError(
                "Начать можно только запланированное занятие", details={"status": session.status}
            )
        updated = replace(
            session,
            status=SessionStatus.IN_PROGRESS,
            started_at=self._clock.now(),
        )
        return await self._session_view(await self._sessions.save_session(updated))

    async def complete_session(self, session_id: str, score: int | None) -> SessionView:
        session = await require_session(self._sessions, session_id)
        if session.status != SessionStatus.IN_PROGRESS:
            raise InvalidStateError(
                "Завершить можно только начатое занятие", details={"status": session.status}
            )
        updated = replace(
            session,
            status=SessionStatus.COMPLETED,
            completed_at=self._clock.now(),
            score=score,
        )
        return await self._session_view(await self._sessions.save_session(updated))

    async def reschedule_session(self, session_id: str, scheduled_for: datetime) -> SessionView:
        session = await require_session(self._sessions, session_id)
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError("Перенести можно только запланированное занятие")
        updated = replace(session, scheduled_for=scheduled_for)
        return await self._session_view(await self._sessions.save_session(updated))

    async def delete_session(self, session_id: str) -> None:
        session = await require_session(self._sessions, session_id)
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError(
                "Удалить можно только запланированное занятие",
                details={"status": session.status},
            )
        await self._sessions.delete_session(session_id)

    async def _session_view(self, session: StudySession) -> SessionView:
        lesson = await self._catalog.get_lesson(session.lesson_id)
        return SessionView(
            **self._session_values(session),
            lesson_title=lesson.title if lesson else "Неизвестный урок",
        )

    @staticmethod
    def _session_values(session: StudySession) -> dict[str, object]:
        return {
            "id": session.id,
            "plan_id": session.plan_id,
            "lesson_id": session.lesson_id,
            "scheduled_for": session.scheduled_for,
            "duration_minutes": session.duration_minutes,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "score": session.score,
        }
