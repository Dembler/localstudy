from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.domain.entities import (
    Course,
    CourseLevel,
    Lesson,
)
from src.infrastructure.models import (
    CourseModel,
    LessonModel,
)


class SqlAlchemyCatalogRepository:
    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def list_courses(self, *, level: str | None = None, skill: str | None = None) -> list[Course]:
        statement = select(CourseModel).order_by(CourseModel.title)
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
        statement = select(LessonModel).order_by(LessonModel.course_id, LessonModel.position)
        if course_ids is not None:
            if not course_ids:
                return []
            statement = statement.where(LessonModel.course_id.in_(course_ids))
        return [self._lesson(row) for row in (await self._session.scalars(statement)).all()]

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
