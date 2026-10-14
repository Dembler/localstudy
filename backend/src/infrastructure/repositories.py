from datetime import UTC, date, datetime, time, timedelta
from uuid import uuid4

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    Assignment,
    Attempt,
    Course,
    CourseLevel,
    Goal,
    Lesson,
    SessionStatus,
    StudyPlan,
    StudySession,
)
from src.infrastructure.models import (
    AssignmentModel,
    AttemptModel,
    CourseModel,
    GoalModel,
    LessonModel,
    PlanModel,
    SessionModel,
)


class SqlAlchemyLearningRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_courses(self, *, level: str | None = None, skill: str | None = None) -> list[Course]:
        statement: Select[tuple[CourseModel]] = select(CourseModel).order_by(CourseModel.title)
        if level:
            statement = statement.where(CourseModel.level == level)
        rows = (await self._session.scalars(statement)).all()
        courses = [self._course(row) for row in rows]
        if skill:
            skill_key = skill.casefold()
            courses = [
                item for item in courses if any(skill_key in value.casefold() for value in item.skills)
            ]
        return courses

    async def search_courses(self, query: str) -> list[Course]:
        query_key = query.casefold()
        courses = await self.list_courses()
        return [
            item
            for item in courses
            if query_key in item.title.casefold()
            or query_key in item.description.casefold()
            or any(query_key in skill.casefold() for skill in item.skills)
        ]

    async def get_course(self, course_id: str) -> Course | None:
        row = await self._session.get(CourseModel, course_id)
        return self._course(row) if row else None

    async def get_courses(self, course_ids: list[str]) -> list[Course]:
        if not course_ids:
            return []
        rows = (await self._session.scalars(select(CourseModel).where(CourseModel.id.in_(course_ids)))).all()
        by_id = {row.id: self._course(row) for row in rows}
        return [by_id[item] for item in course_ids if item in by_id]

    async def count_lessons_by_course(self, course_ids: list[str]) -> dict[str, int]:
        if not course_ids:
            return {}
        rows = (
            await self._session.execute(
                select(LessonModel.course_id, func.count(LessonModel.id))
                .where(LessonModel.course_id.in_(course_ids))
                .group_by(LessonModel.course_id)
            )
        ).all()
        return {course_id: count for course_id, count in rows}

    async def get_lesson(self, lesson_id: str) -> Lesson | None:
        row = await self._session.get(LessonModel, lesson_id)
        return self._lesson(row) if row else None

    async def list_lessons(self, course_ids: list[str] | None = None) -> list[Lesson]:
        statement: Select[tuple[LessonModel]] = select(LessonModel).order_by(
            LessonModel.course_id, LessonModel.position
        )
        if course_ids is not None:
            if not course_ids:
                return []
            statement = statement.where(LessonModel.course_id.in_(course_ids))
        return [self._lesson(row) for row in (await self._session.scalars(statement)).all()]

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
            raise RuntimeError("plan disappeared during update")
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

    async def list_sessions(
        self, *, from_date: date | None = None, to_date: date | None = None
    ) -> list[StudySession]:
        statement: Select[tuple[SessionModel]] = select(SessionModel).order_by(SessionModel.scheduled_for)
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
        row = await self._session.get(SessionModel, session.id)
        if row is None:
            raise RuntimeError("session disappeared during update")
        row.scheduled_for = self._naive(session.scheduled_for)
        row.duration_minutes = session.duration_minutes
        row.status = session.status
        row.started_at = self._naive(session.started_at) if session.started_at else None
        row.completed_at = self._naive(session.completed_at) if session.completed_at else None
        row.score = session.score
        await self._commit()
        return self._study_session(row)

    async def rebalance_plan_sessions(self, plan: StudyPlan) -> int:
        rows = (
            await self._session.scalars(
                select(SessionModel)
                .where(
                    SessionModel.plan_id == plan.id,
                    SessionModel.status == SessionStatus.PLANNED,
                )
                .order_by(SessionModel.scheduled_for)
            )
        ).all()
        if not rows:
            return 0
        days = [0, 2, 5]
        base = max(date.today(), plan.start_date)
        per_session = max(20, plan.weekly_minutes // len(days))
        for index, row in enumerate(rows):
            week = index // len(days)
            weekday_offset = days[index % len(days)]
            row.scheduled_for = datetime.combine(
                base + timedelta(days=week * 7 + weekday_offset), time(hour=18)
            )
            row.duration_minutes = min(180, per_session)
        await self._commit()
        return len(rows)

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
        if row:
            row.hint_requested = True
            await self._commit()

    async def consume_hint_marker(self, assignment_id: str) -> bool:
        row = await self._session.scalar(
            select(AssignmentModel).where(AssignmentModel.id == assignment_id).with_for_update()
        )
        if row is None:
            return False
        value = row.hint_requested
        row.hint_requested = False
        # Keep the marker update in the same transaction as attempt creation.
        # create_attempt() commits both changes or rolls them back together.
        await self._session.flush()
        return value

    async def clear_hint_marker(self, assignment_id: str) -> None:
        row = await self._session.scalar(
            select(AssignmentModel).where(AssignmentModel.id == assignment_id).with_for_update()
        )
        if row is None:
            return
        row.hint_requested = False
        await self._commit()

    async def create_attempt(
        self, *, assignment_id: str, answer: str, is_correct: bool, score: int, hint_used: bool
    ) -> Attempt:
        row = AttemptModel(
            id=str(uuid4()),
            assignment_id=assignment_id,
            answer=answer,
            is_correct=is_correct,
            score=score,
            hint_used=hint_used,
            created_at=self._now(),
        )
        self._session.add(row)
        await self._commit()
        return self._attempt(row)

    async def list_attempts(self, assignment_id: str | None = None) -> list[Attempt]:
        statement: Select[tuple[AttemptModel]] = select(AttemptModel).order_by(AttemptModel.created_at)
        if assignment_id:
            statement = statement.where(AttemptModel.assignment_id == assignment_id)
        return [self._attempt(row) for row in (await self._session.scalars(statement)).all()]

    async def answer_for(self, assignment_id: str) -> str | None:
        row = await self._session.get(AssignmentModel, assignment_id)
        return row.expected_answer if row else None

    async def _commit(self) -> None:
        try:
            await self._session.commit()
        except Exception:
            await self._session.rollback()
            raise

    @staticmethod
    def _course(row: CourseModel) -> Course:
        return Course(
            id=row.id,
            slug=row.slug,
            title=row.title,
            description=row.description,
            level=CourseLevel(row.level),
            duration_minutes=row.duration_minutes,
            skills=list(row.skills),
            prerequisite_ids=list(row.prerequisite_ids),
        )

    @staticmethod
    def _lesson(row: LessonModel) -> Lesson:
        return Lesson(
            id=row.id,
            course_id=row.course_id,
            title=row.title,
            summary=row.summary,
            preview=row.preview,
            duration_minutes=row.duration_minutes,
            position=row.position,
        )

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

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)

    @staticmethod
    def _naive(value: datetime) -> datetime:
        return value.astimezone(UTC).replace(tzinfo=None) if value.tzinfo else value
