from datetime import UTC, date, datetime, time
from uuid import uuid4

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    SessionStatus,
    StudySession,
)
from src.domain.exceptions import InvalidStateError, NotFoundError
from src.infrastructure.models import (
    SessionModel,
)


class SqlAlchemySessionRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_sessions(
        self, *, from_date: date | None = None, to_date: date | None = None
    ) -> list[StudySession]:
        statement = select(SessionModel).order_by(SessionModel.scheduled_for)
        if from_date:
            statement = statement.where(SessionModel.scheduled_for >= datetime.combine(from_date, time.min))
        if to_date:
            statement = statement.where(SessionModel.scheduled_for <= datetime.combine(to_date, time.max))
        return [self._study_session(row) for row in (await self._session.scalars(statement)).all()]

    async def list_plan_sessions(self, plan_id: str) -> list[StudySession]:
        rows = await self._session.scalars(
            select(SessionModel).where(SessionModel.plan_id == plan_id).order_by(SessionModel.scheduled_for)
        )
        return [self._study_session(row) for row in rows.all()]

    async def create_session(
        self,
        *,
        plan_id: str,
        lesson_id: str,
        scheduled_for: datetime,
        duration_minutes: int,
    ) -> StudySession:
        row = SessionModel(
            id=str(uuid4()),
            plan_id=plan_id,
            lesson_id=lesson_id,
            scheduled_for=self._naive(scheduled_for),
            duration_minutes=duration_minutes,
            status=SessionStatus.PLANNED,
        )
        self._session.add(row)
        await self._commit()
        return self._study_session(row)

    async def get_session(self, session_id: str) -> StudySession | None:
        row = await self._session.get(SessionModel, session_id)
        return self._study_session(row) if row else None

    async def save_session(self, session: StudySession) -> StudySession:
        await self.save_sessions([session])
        row = await self._session.get(SessionModel, session.id)
        assert row is not None
        return self._study_session(row)

    async def save_sessions(self, sessions: list[StudySession]) -> None:
        if not sessions:
            return
        try:
            rows = list(
                await self._session.scalars(
                    select(SessionModel).where(SessionModel.id.in_([item.id for item in sessions]))
                )
            )
            by_id = {row.id: row for row in rows}
            for session in sessions:
                if session.id not in by_id:
                    raise NotFoundError("Учебное занятие не найдено", details={"session_id": session.id})
                row = by_id[session.id]
                row.scheduled_for = self._naive(session.scheduled_for)
                row.duration_minutes = session.duration_minutes
                row.status = session.status
                row.started_at = self._naive(session.started_at) if session.started_at else None
                row.completed_at = self._naive(session.completed_at) if session.completed_at else None
                row.score = session.score
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def delete_session(self, session_id: str) -> None:
        row = await self._session.get(SessionModel, session_id)
        if row is None:
            raise NotFoundError("Учебное занятие не найдено", details={"session_id": session_id})
        if SessionStatus(row.status) != SessionStatus.PLANNED:
            raise InvalidStateError(
                "Удалить можно только запланированное занятие",
                details={"status": row.status},
            )
        try:
            await self._session.delete(row)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _study_session(row: SessionModel) -> StudySession:
        return StudySession(
            id=row.id,
            plan_id=row.plan_id,
            lesson_id=row.lesson_id,
            scheduled_for=row.scheduled_for,
            duration_minutes=row.duration_minutes,
            status=SessionStatus(row.status),
            started_at=row.started_at,
            completed_at=row.completed_at,
            score=row.score,
        )

    @staticmethod
    def _naive(value: datetime) -> datetime:
        return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise
