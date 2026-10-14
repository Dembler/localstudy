from datetime import UTC, date, datetime
from uuid import uuid4

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    Goal,
    SessionStatus,
    StudyPlan,
)
from src.domain.exceptions import ConflictError, NotFoundError
from src.infrastructure.models import (
    GoalModel,
    PlanModel,
    SessionModel,
)


class SqlAlchemyPlanRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create_plan(
        self, *, name: str, weekly_minutes: int, start_date: date, course_ids: list[str]
    ) -> StudyPlan:
        row = PlanModel(
            id=str(uuid4()),
            name=name,
            weekly_minutes=weekly_minutes,
            start_date=start_date,
            course_ids=course_ids,
            created_at=self._now(),
        )
        self._session.add(row)
        await self._commit()
        return self._plan(row)

    async def get_plan(self, plan_id: str) -> StudyPlan | None:
        row = await self._session.get(PlanModel, plan_id)
        return self._plan(row) if row else None

    async def list_plans(self) -> list[StudyPlan]:
        rows = (await self._session.scalars(select(PlanModel).order_by(PlanModel.created_at))).all()
        return [self._plan(row) for row in rows]

    async def update_plan_workload(self, plan_id: str, weekly_minutes: int) -> StudyPlan:
        row = await self._session.get(PlanModel, plan_id)
        if row is None:
            raise NotFoundError("Учебный план не найден", details={"plan_id": plan_id})
        row.weekly_minutes = weekly_minutes
        await self._commit()
        return self._plan(row)

    async def add_goal(self, *, plan_id: str, title: str, target_date: date, target_minutes: int) -> Goal:
        row = GoalModel(
            id=str(uuid4()),
            plan_id=plan_id,
            title=title,
            target_date=target_date,
            target_minutes=target_minutes,
            progress_percent=0,
        )
        self._session.add(row)
        await self._commit()
        return self._goal(row)

    async def delete_plan(self, plan_id: str) -> None:
        row = await self._session.get(PlanModel, plan_id)
        if row is None:
            raise NotFoundError("Учебный план не найден", details={"plan_id": plan_id})
        try:
            await self._session.execute(delete(GoalModel).where(GoalModel.plan_id == plan_id))
            await self._session.execute(delete(SessionModel).where(SessionModel.plan_id == plan_id))
            await self._session.delete(row)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def delete_goal(self, plan_id: str, goal_id: str) -> None:
        row = await self._session.scalar(
            select(GoalModel).where(GoalModel.id == goal_id, GoalModel.plan_id == plan_id)
        )
        if row is None:
            raise NotFoundError(
                "Цель учебного плана не найдена",
                details={"plan_id": plan_id, "goal_id": goal_id},
            )
        try:
            await self._session.delete(row)
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    async def remove_course(self, plan_id: str, course_id: str, lesson_ids: list[str]) -> StudyPlan:
        row = await self._session.get(PlanModel, plan_id)
        if row is None:
            raise NotFoundError("Учебный план не найден", details={"plan_id": plan_id})
        if course_id not in row.course_ids:
            raise NotFoundError(
                "Курс не найден в учебном плане",
                details={"plan_id": plan_id, "course_id": course_id},
            )
        if len(row.course_ids) == 1:
            raise ConflictError("Нельзя удалить последний курс учебного плана")
        try:
            row.course_ids = [item for item in row.course_ids if item != course_id]
            if lesson_ids:
                await self._session.execute(
                    delete(SessionModel).where(
                        SessionModel.plan_id == plan_id,
                        SessionModel.lesson_id.in_(lesson_ids),
                        SessionModel.status == SessionStatus.PLANNED,
                    )
                )
            await self._session.commit()
            return self._plan(row)
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _plan(row: PlanModel) -> StudyPlan:
        return StudyPlan(
            id=row.id,
            name=row.name,
            weekly_minutes=row.weekly_minutes,
            start_date=row.start_date,
            course_ids=list(row.course_ids),
            created_at=row.created_at,
        )

    @staticmethod
    def _goal(row: GoalModel) -> Goal:
        return Goal(
            id=row.id,
            plan_id=row.plan_id,
            title=row.title,
            target_date=row.target_date,
            target_minutes=row.target_minutes,
            progress_percent=row.progress_percent,
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
