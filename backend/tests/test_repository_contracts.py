import asyncio
from collections.abc import AsyncIterator
from dataclasses import asdict, dataclass, replace
from datetime import UTC, date, datetime, timedelta, timezone

import pytest

from src.application.ports import CatalogReader, PlanRepository, PracticeRepository, SessionRepository
from src.domain.entities import (
    AnswerEvaluation,
    Assignment,
    Course,
    CourseLevel,
    Lesson,
    SessionStatus,
    StudyPlan,
    StudySession,
)
from src.domain.exceptions import ConflictError, InvalidStateError, NotFoundError
from src.infrastructure.database import Base, make_engine, make_session_factory
from src.infrastructure.models import AssignmentModel, CourseModel, LessonModel, PlanModel, SessionModel
from src.infrastructure.repositories import (
    SqlAlchemyCatalogRepository,
    SqlAlchemyPlanRepository,
    SqlAlchemyPracticeRepository,
    SqlAlchemySessionRepository,
)
from tests.memory_repositories import MemoryCatalog, MemoryPlans, MemoryPractice, MemorySessions

TODAY = date(2026, 10, 14)
NOW = datetime(2026, 10, 14, 12)
COURSES = [
    Course("b", "beta", "Beta", "Advanced course", CourseLevel.ADVANCED, 60, ["SQL"], ["a"]),
    Course("a", "alpha", "Alpha", "Basic course", CourseLevel.BEGINNER, 30, ["Python"]),
]
LESSONS = [
    Lesson("la", "a", "Lesson A", "Summary", "Preview", 30, 1),
    Lesson("lb", "b", "Lesson B", "Summary", "Preview", 60, 1),
]
PLANS = [StudyPlan("p", "Plan", 180, TODAY, ["a", "b"], NOW)]
SESSIONS = [StudySession("s", "p", "la", NOW, 30, SessionStatus.PLANNED)]
ASSIGNMENTS = [Assignment("q", "la", "Types", "Question", "Hint", 1)]


@dataclass
class Repositories:
    catalog: CatalogReader
    plans: PlanRepository
    sessions: SessionRepository
    practice: PracticeRepository


@pytest.fixture(params=["memory", "sqlalchemy"])
async def repositories(request, tmp_path) -> AsyncIterator[Repositories]:
    if request.param == "memory":
        sessions = MemorySessions(SESSIONS)
        yield Repositories(
            MemoryCatalog(COURSES, LESSONS),
            MemoryPlans(PLANS, sessions.sessions),
            sessions,
            MemoryPractice(ASSIGNMENTS, {"q": "bool"}),
        )
        return
    engine = make_engine(f"sqlite+aiosqlite:///{(tmp_path / 'contracts.db').as_posix()}")
    try:
        async with engine.begin() as connection:
            await connection.run_sync(Base.metadata.create_all)
        async with make_session_factory(engine)() as session:
            session.add_all([CourseModel(**asdict(item)) for item in COURSES])
            session.add_all([LessonModel(**asdict(item)) for item in LESSONS])
            session.add_all([PlanModel(**asdict(item)) for item in PLANS])
            session.add_all([SessionModel(**asdict(item)) for item in SESSIONS])
            session.add_all(
                [
                    AssignmentModel(**asdict(item), expected_answer="bool", hint_requested=False)
                    for item in ASSIGNMENTS
                ]
            )
            await session.commit()
            yield Repositories(
                SqlAlchemyCatalogRepository(session),
                SqlAlchemyPlanRepository(session),
                SqlAlchemySessionRepository(session),
                SqlAlchemyPracticeRepository(session),
            )
    finally:
        await engine.dispose()


async def test_catalog_order_filters_and_detached_values(repositories: Repositories) -> None:
    catalog = repositories.catalog
    assert [item.id for item in await catalog.list_courses()] == ["a", "b"]
    assert [item.id for item in await catalog.list_courses(level="beginner", skill="PYT")] == ["a"]
    assert [item.id for item in await catalog.search_courses("sql")] == ["b"]
    assert [item.id for item in await catalog.get_courses(["b", "missing", "a"])] == ["b", "a"]
    assert await catalog.get_courses([]) == []
    assert await catalog.get_course("missing") is None
    course = await catalog.get_course("a")
    assert course is not None
    course.skills.append("mutated")
    assert (await catalog.get_course("a")).skills == ["Python"]
    assert await catalog.list_lessons([]) == []
    assert [item.id for item in await catalog.list_lessons(["a"])] == ["la"]
    assert (await catalog.get_lesson("la")).course_id == "a"
    assert await catalog.get_lesson("missing") is None
    assert await catalog.count_lessons_by_course(["a", "missing"]) == {"a": 1}


async def test_plan_write_read_and_missing_update(repositories: Repositories) -> None:
    plans = repositories.plans
    created = await plans.create_plan(name="New plan", weekly_minutes=240, start_date=TODAY, course_ids=["a"])
    assert created.id
    assert (await plans.get_plan(created.id)).weekly_minutes == 240
    assert [item.id for item in await plans.list_plans()] == ["p", created.id]
    created.course_ids.append("changed")
    assert (await plans.get_plan(created.id)).course_ids == ["a"]
    updated = await plans.update_plan_workload(created.id, 300)
    assert updated.weekly_minutes == (await plans.get_plan(created.id)).weekly_minutes == 300
    goal = await plans.add_goal(plan_id=created.id, title="Finish", target_date=TODAY, target_minutes=90)
    assert goal.plan_id == created.id and goal.progress_percent == 0
    await plans.delete_goal(created.id, goal.id)
    with pytest.raises(NotFoundError):
        await plans.delete_goal(created.id, goal.id)

    updated_courses = await plans.remove_course("p", "b", ["lb"])
    assert updated_courses.course_ids == ["a"]
    with pytest.raises(ConflictError):
        await plans.remove_course("p", "a", ["la"])

    await plans.delete_plan("p")
    assert await plans.get_plan("p") is None
    assert await repositories.sessions.list_plan_sessions("p") == []
    with pytest.raises(NotFoundError):
        await plans.delete_plan("p")
    assert await plans.get_plan("missing") is None
    with pytest.raises(NotFoundError):
        await plans.update_plan_workload("missing", 180)


async def test_session_dates_lifecycle_and_atomic_batch(repositories: Repositories) -> None:
    sessions = repositories.sessions
    aware = datetime(2026, 10, 15, 15, tzinfo=timezone(timedelta(hours=3)))
    created = await sessions.create_session(
        plan_id="p", lesson_id="lb", scheduled_for=aware, duration_minutes=45
    )
    assert created.status == SessionStatus.PLANNED
    assert created.scheduled_for == aware.astimezone(UTC).replace(tzinfo=None)
    assert [item.id for item in await sessions.list_sessions(from_date=TODAY, to_date=TODAY)] == ["s"]
    assert [item.id for item in await sessions.list_plan_sessions("p")] == ["s", created.id]
    assert await sessions.list_plan_sessions("missing") == []
    original = await sessions.get_session("s")
    assert original is not None
    with pytest.raises(NotFoundError):
        await sessions.save_sessions(
            [replace(original, duration_minutes=99), replace(original, id="missing")]
        )
    assert (await sessions.get_session("s")).duration_minutes == 30
    updated = await sessions.save_session(
        replace(original, status=SessionStatus.COMPLETED, completed_at=aware, score=88)
    )
    assert updated.score == 88 and updated.status == SessionStatus.COMPLETED
    assert updated.completed_at == aware.astimezone(UTC).replace(tzinfo=None)
    with pytest.raises(InvalidStateError):
        await sessions.delete_session("s")
    await sessions.delete_session(created.id)
    assert await sessions.get_session(created.id) is None
    with pytest.raises(NotFoundError):
        await sessions.delete_session(created.id)
    await sessions.save_sessions([])
    assert await sessions.get_session("missing") is None


async def test_practice_hint_is_consumed_once_and_retry_clears_it(repositories: Repositories) -> None:
    practice = repositories.practice
    assert (await practice.get_assignment("q")).lesson_id == "la"
    assert await practice.get_assignment("missing") is None
    assert await practice.answer_for("missing") is None
    assert await practice.answer_for("q") == "bool"
    assert [item.id for item in await practice.list_assignments()] == ["q"]
    grade = AnswerEvaluation(True, 90, 70)
    await practice.mark_hint_requested("q")
    first = await practice.record_attempt(assignment_id="q", answer="bool", evaluation=grade)
    second = await practice.record_attempt(assignment_id="q", answer="bool", evaluation=grade)
    assert first.hint_used and first.score == 70
    assert not second.hint_used and second.score == 90
    await practice.mark_hint_requested("q")
    await practice.clear_hint_marker("q")
    third = await practice.record_attempt(assignment_id="q", answer="bool", evaluation=grade)
    assert not third.hint_used
    assert [item.id for item in await practice.list_attempts("q")] == [first.id, second.id, third.id]
    assert await practice.list_attempts("missing") == []
    assert len(await practice.list_attempts()) == 3
    with pytest.raises(NotFoundError):
        await practice.record_attempt(assignment_id="missing", answer="x", evaluation=grade)
    with pytest.raises(NotFoundError):
        await practice.mark_hint_requested("missing")
    with pytest.raises(NotFoundError):
        await practice.clear_hint_marker("missing")


@pytest.mark.parametrize("repositories", ["sqlalchemy"], indirect=True)
async def test_failed_attempt_preserves_hint_and_does_not_persist_partial_data(
    repositories: Repositories, monkeypatch
) -> None:
    practice = repositories.practice
    assert isinstance(practice, SqlAlchemyPracticeRepository)
    await practice.mark_hint_requested("q")
    session = practice._session
    original_commit = session.commit

    async def fail_commit() -> None:
        raise RuntimeError("Simulated storage failure")

    monkeypatch.setattr(session, "commit", fail_commit)
    with pytest.raises(RuntimeError, match="Simulated storage failure"):
        await practice.record_attempt(
            assignment_id="q", answer="bool", evaluation=AnswerEvaluation(True, 100, 85)
        )
    monkeypatch.setattr(session, "commit", original_commit)
    assert await practice.list_attempts() == []
    retried = await practice.record_attempt(
        assignment_id="q", answer="bool", evaluation=AnswerEvaluation(True, 100, 85)
    )
    assert retried.hint_used and retried.score == 85


@pytest.mark.parametrize("repositories", ["sqlalchemy"], indirect=True)
async def test_concurrent_attempts_consume_a_hint_only_once(repositories: Repositories) -> None:
    practice = repositories.practice
    assert isinstance(practice, SqlAlchemyPracticeRepository)
    await practice.mark_hint_requested("q")
    factory = make_session_factory(practice._session.bind)

    async def submit():
        async with factory() as session:
            return await SqlAlchemyPracticeRepository(session).record_attempt(
                assignment_id="q", answer="bool", evaluation=AnswerEvaluation(True, 100, 85)
            )

    attempts = await asyncio.gather(submit(), submit())
    assert sorted(item.score for item in attempts) == [85, 100]
    assert sum(item.hint_used for item in attempts) == 1
