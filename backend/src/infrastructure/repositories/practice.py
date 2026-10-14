from datetime import UTC, datetime
from uuid import uuid4

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    AnswerEvaluation,
    Assignment,
    Attempt,
)
from src.domain.exceptions import NotFoundError
from src.infrastructure.models import (
    AssignmentModel,
    AttemptModel,
)


class SqlAlchemyPracticeRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def get_assignment(self, assignment_id: str) -> Assignment | None:
        row = await self._session.get(AssignmentModel, assignment_id)
        return self._assignment(row) if row else None

    async def list_assignments(self) -> list[Assignment]:
        rows = (
            await self._session.scalars(select(AssignmentModel).order_by(AssignmentModel.difficulty))
        ).all()
        return [self._assignment(row) for row in rows]

    async def mark_hint_requested(self, assignment_id: str) -> None:
        row = await self._session.get(AssignmentModel, assignment_id)
        if row is None:
            raise NotFoundError("Задание не найдено", details={"assignment_id": assignment_id})
        row.hint_requested = True
        await self._commit()

    async def clear_hint_marker(self, assignment_id: str) -> None:
        row = await self._session.scalar(
            select(AssignmentModel).where(AssignmentModel.id == assignment_id).with_for_update()
        )
        if row is None:
            raise NotFoundError("Задание не найдено", details={"assignment_id": assignment_id})
        row.hint_requested = False
        await self._commit()

    async def record_attempt(
        self, *, assignment_id: str, answer: str, evaluation: AnswerEvaluation
    ) -> Attempt:
        try:
            hinted_id = await self._session.scalar(
                update(AssignmentModel)
                .where(AssignmentModel.id == assignment_id, AssignmentModel.hint_requested.is_(True))
                .values(hint_requested=False)
                .returning(AssignmentModel.id)
            )
            hint_used = hinted_id is not None
            if not hint_used and await self._session.get(AssignmentModel, assignment_id) is None:
                raise NotFoundError("Задание не найдено", details={"assignment_id": assignment_id})
            row = AttemptModel(
                id=str(uuid4()),
                assignment_id=assignment_id,
                answer=answer,
                is_correct=evaluation.is_correct,
                score=evaluation.hinted_score if hint_used else evaluation.score,
                hint_used=hint_used,
                created_at=self._now(),
            )
            self._session.add(row)
            await self._session.commit()
            return self._attempt(row)
        except Exception:
            await self._session.rollback()
            raise

    async def list_attempts(self, assignment_id: str | None = None) -> list[Attempt]:
        statement = select(AttemptModel).order_by(AttemptModel.created_at)
        if assignment_id:
            statement = statement.where(AttemptModel.assignment_id == assignment_id)
        return [self._attempt(row) for row in (await self._session.scalars(statement)).all()]

    async def answer_for(self, assignment_id: str) -> str | None:
        row = await self._session.get(AssignmentModel, assignment_id)
        return row.expected_answer if row else None

    @staticmethod
    def _assignment(row: AssignmentModel) -> Assignment:
        return Assignment(
            id=row.id,
            lesson_id=row.lesson_id,
            topic=row.topic,
            prompt=row.prompt,
            hint=row.hint,
            difficulty=row.difficulty,
        )

    @staticmethod
    def _attempt(row: AttemptModel) -> Attempt:
        return Attempt(
            id=row.id,
            assignment_id=row.assignment_id,
            answer=row.answer,
            is_correct=row.is_correct,
            score=row.score,
            hint_used=row.hint_used,
            created_at=row.created_at,
        )

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)
