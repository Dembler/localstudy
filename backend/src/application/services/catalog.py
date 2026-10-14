from src.application.ports import CatalogReader
from src.application.schemas import (
    CourseDetail,
    CourseList,
    CourseSummary,
    LessonPreview,
)
from src.application.services.lookups import require_course
from src.application.services.prerequisites import PrerequisiteResolver
from src.domain.entities import Course
from src.domain.exceptions import NotFoundError


class CatalogService:
    def __init__(self, catalog: CatalogReader, prerequisites: PrerequisiteResolver) -> None:
        self._catalog = catalog
        self._prerequisites = prerequisites

    async def list_courses(self, level: str | None, skill: str | None) -> CourseList:
        courses = await self._catalog.list_courses(level=level, skill=skill)
        return CourseList(items=await self._course_summaries(courses), total=len(courses))

    async def search_courses(self, query: str) -> CourseList:
        courses = await self._catalog.search_courses(query)
        return CourseList(items=await self._course_summaries(courses), total=len(courses))

    async def get_course(self, course_id: str) -> CourseDetail:
        course = await require_course(self._catalog, course_id)
        summary = (await self._course_summaries([course]))[0]
        return CourseDetail(
            **summary.model_dump(),
            prerequisite_ids=course.prerequisite_ids,
        )

    async def prerequisites(self, course_id: str) -> CourseList:
        course = await require_course(self._catalog, course_id)
        direct_prerequisites = await self._catalog.get_courses(course.prerequisite_ids)
        prerequisite_ids = await self._prerequisites.expand(direct_prerequisites)
        prerequisites = await self._catalog.get_courses(prerequisite_ids)
        return CourseList(items=await self._course_summaries(prerequisites), total=len(prerequisites))

    async def lesson_preview(self, lesson_id: str) -> LessonPreview:
        lesson = await self._catalog.get_lesson(lesson_id)
        if lesson is None:
            raise NotFoundError("Урок не найден", details={"lesson_id": lesson_id})
        return LessonPreview(
            **lesson.__dict__
            if hasattr(lesson, "__dict__")
            else {
                "id": lesson.id,
                "course_id": lesson.course_id,
                "title": lesson.title,
                "summary": lesson.summary,
                "preview": lesson.preview,
                "duration_minutes": lesson.duration_minutes,
                "position": lesson.position,
            }
        )

    async def _course_summaries(self, courses: list[Course]) -> list[CourseSummary]:
        lesson_counts = await self._catalog.count_lessons_by_course([course.id for course in courses])
        return [self._course_summary(course, lesson_counts.get(course.id, 0)) for course in courses]

    @staticmethod
    def _course_summary(course: Course, lesson_count: int) -> CourseSummary:
        return CourseSummary(
            id=course.id,
            slug=course.slug,
            title=course.title,
            description=course.description,
            level=course.level,
            duration_minutes=course.duration_minutes,
            skills=course.skills,
            lesson_count=lesson_count,
        )
