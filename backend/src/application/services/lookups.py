from src.application.ports import CatalogReader, PlanReader, PracticeReader, SessionReader
from src.domain.entities import Assignment, Course, Lesson, StudyPlan, StudySession
from src.domain.exceptions import NotFoundError


async def require_course(repository: CatalogReader, course_id: str) -> Course:
    course = await repository.get_course(course_id)
    if course is None:
        raise NotFoundError("Курс не найден", details={"course_id": course_id})
    return course


async def require_lesson(repository: CatalogReader, lesson_id: str) -> Lesson:
    lesson = await repository.get_lesson(lesson_id)
    if lesson is None:
        raise NotFoundError("Урок не найден", details={"lesson_id": lesson_id})
    return lesson


async def require_plan(repository: PlanReader, plan_id: str) -> StudyPlan:
    plan = await repository.get_plan(plan_id)
    if plan is None:
        raise NotFoundError("Учебный план не найден", details={"plan_id": plan_id})
    return plan


async def require_session(repository: SessionReader, session_id: str) -> StudySession:
    session = await repository.get_session(session_id)
    if session is None:
        raise NotFoundError("Учебное занятие не найдено", details={"session_id": session_id})
    return session


async def require_assignment(repository: PracticeReader, assignment_id: str) -> Assignment:
    assignment = await repository.get_assignment(assignment_id)
    if assignment is None:
        raise NotFoundError("Задание не найдено", details={"assignment_id": assignment_id})
    return assignment
