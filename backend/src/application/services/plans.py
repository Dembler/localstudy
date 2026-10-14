import logging
import math
from datetime import date, timedelta

from src.application.policies.scheduling import SchedulePolicy
from src.application.ports import (
    CatalogReader,
    Clock,
    PlanRepository,
    SessionRepository,
)
from src.application.schemas import (
    ForecastView,
    GoalView,
    PlanView,
    RebalanceResult,
)
from src.application.services.lookups import require_plan
from src.application.services.prerequisites import PrerequisiteResolver
from src.domain.entities import (
    SessionStatus,
    StudyPlan,
)
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError


class PlanService:
    def __init__(
        self,
        plans: PlanRepository,
        catalog: CatalogReader,
        sessions: SessionRepository,
        prerequisites: PrerequisiteResolver,
        scheduler: SchedulePolicy,
        clock: Clock,
        logger: logging.Logger,
    ) -> None:
        self._plans = plans
        self._catalog = catalog
        self._sessions = sessions
        self._prerequisites = prerequisites
        self._scheduler = scheduler
        self._clock = clock
        self._logger = logger

    async def create_plan(
        self, *, name: str, weekly_minutes: int, start_date: date, course_ids: list[str]
    ) -> PlanView:
        unique_ids = list(dict.fromkeys(course_ids))
        courses = await self._catalog.get_courses(unique_ids)
        if len(courses) != len(unique_ids):
            found = {course.id for course in courses}
            raise NotFoundError(
                "Один или несколько курсов не найдены",
                details={"missing_course_ids": [item for item in unique_ids if item not in found]},
            )
        expanded = await self._prerequisites.expand(courses)
        plan = await self._plans.create_plan(
            name=name,
            weekly_minutes=weekly_minutes,
            start_date=start_date,
            course_ids=expanded,
        )
        self._logger.info("study plan created", extra={"plan_id": plan.id})
        return self._plan_view(plan)

    async def update_workload(self, plan_id: str, weekly_minutes: int) -> PlanView:
        await require_plan(self._plans, plan_id)
        plan = await self._plans.update_plan_workload(plan_id, weekly_minutes)
        return self._plan_view(plan)

    async def add_goal(self, *, plan_id: str, title: str, target_date: date, target_minutes: int) -> GoalView:
        await require_plan(self._plans, plan_id)
        if target_date < self._clock.today():
            raise ValidationError("Дата цели не может быть в прошлом")
        goal = await self._plans.add_goal(
            plan_id=plan_id,
            title=title,
            target_date=target_date,
            target_minutes=target_minutes,
        )
        return GoalView(
            **{
                "id": goal.id,
                "plan_id": goal.plan_id,
                "title": goal.title,
                "target_date": goal.target_date,
                "target_minutes": goal.target_minutes,
                "progress_percent": goal.progress_percent,
            }
        )

    async def delete_plan(self, plan_id: str) -> None:
        await require_plan(self._plans, plan_id)
        await self._plans.delete_plan(plan_id)
        self._logger.info("study plan deleted", extra={"plan_id": plan_id})

    async def delete_goal(self, plan_id: str, goal_id: str) -> None:
        await require_plan(self._plans, plan_id)
        await self._plans.delete_goal(plan_id, goal_id)

    async def remove_course(self, plan_id: str, course_id: str) -> None:
        plan = await require_plan(self._plans, plan_id)
        if course_id not in plan.course_ids:
            raise NotFoundError(
                "Курс не найден в учебном плане",
                details={"plan_id": plan_id, "course_id": course_id},
            )
        if len(plan.course_ids) == 1:
            raise ConflictError("Нельзя удалить последний курс учебного плана")

        remaining_courses = await self._catalog.get_courses(
            [item for item in plan.course_ids if item != course_id]
        )
        required_ids = await self._prerequisites.expand(remaining_courses)
        if course_id in required_ids:
            raise ConflictError(
                "Курс является обязательным пререквизитом для оставшегося маршрута",
                details={"plan_id": plan_id, "course_id": course_id},
            )

        lessons = await self._catalog.list_lessons([course_id])
        lesson_ids = [item.id for item in lessons]
        sessions = await self._sessions.list_plan_sessions(plan_id)
        if any(
            item.lesson_id in lesson_ids and item.status == SessionStatus.IN_PROGRESS for item in sessions
        ):
            raise ConflictError(
                "Нельзя удалить курс, пока идёт занятие по этому курсу",
                details={"plan_id": plan_id, "course_id": course_id},
            )
        await self._plans.remove_course(plan_id, course_id, lesson_ids)

    async def rebalance(self, plan_id: str) -> RebalanceResult:
        plan = await require_plan(self._plans, plan_id)
        sessions = await self._sessions.list_plan_sessions(plan.id)
        updated = self._scheduler.distribute(plan, sessions, self._clock.today())
        await self._sessions.save_sessions(updated)
        return RebalanceResult(
            plan_id=plan.id,
            sessions_updated=len(updated),
            weekly_minutes=plan.weekly_minutes,
            message="Запланированные занятия распределены по доступным учебным дням",
        )

    async def forecast(self, plan_id: str) -> ForecastView:
        plan = await require_plan(self._plans, plan_id)
        lessons = await self._catalog.list_lessons(plan.course_ids)
        sessions = await self._sessions.list_plan_sessions(plan.id)
        completed_lesson_ids = {
            session.lesson_id for session in sessions if session.status == SessionStatus.COMPLETED
        }
        completed_minutes = sum(
            lesson.duration_minutes for lesson in lessons if lesson.id in completed_lesson_ids
        )
        remaining = max(0, sum(item.duration_minutes for item in lessons) - completed_minutes)
        weeks = math.ceil(remaining / plan.weekly_minutes) if remaining else 0
        expected = self._clock.today() + timedelta(weeks=weeks)
        completed_count = len(completed_lesson_ids)
        confidence = "high" if completed_count >= 3 else "medium" if completed_count else "low"
        return ForecastView(
            plan_id=plan.id,
            remaining_minutes=remaining,
            weekly_minutes=plan.weekly_minutes,
            expected_completion=expected,
            weeks_remaining=weeks,
            confidence=confidence,
        )

    @staticmethod
    def _plan_view(plan: StudyPlan) -> PlanView:
        return PlanView(
            id=plan.id,
            name=plan.name,
            weekly_minutes=plan.weekly_minutes,
            start_date=plan.start_date,
            course_ids=plan.course_ids,
            created_at=plan.created_at,
        )
