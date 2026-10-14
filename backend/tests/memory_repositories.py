"""Independent reference adapters for the repository contract tests."""

from copy import deepcopy
from dataclasses import replace
from datetime import UTC, date, datetime
from uuid import uuid4

from src.domain.entities import (
    AnswerEvaluation,
    Assignment,
    Attempt,
    Course,
    Goal,
    Lesson,
    SessionStatus,
    StudyPlan,
    StudySession,
)
from src.domain.exceptions import ConflictError, InvalidStateError, NotFoundError


class MemoryCatalog:
    def __init__(self, courses: list[Course], lessons: list[Lesson]) -> None:
        self.courses = deepcopy(courses)
        self.lessons = deepcopy(lessons)

    async def list_courses(self, *, level: str | None = None, skill: str | None = None) -> list[Course]:
        return deepcopy(
            sorted(
                (
                    course
                    for course in self.courses
                    if (not level or course.level == level)
                    and (not skill or any(skill.casefold() in value.casefold() for value in course.skills))
                ),
                key=lambda course: course.title,
            )
        )

    async def search_courses(self, query: str) -> list[Course]:
        needle = query.casefold()
        return [
            item
            for item in await self.list_courses()
            if any(needle in text.casefold() for text in [item.title, item.description, *item.skills])
        ]

    async def get_course(self, course_id: str) -> Course | None:
        return next((deepcopy(item) for item in self.courses if item.id == course_id), None)

    async def get_courses(self, course_ids: list[str]) -> list[Course]:
        result = []
        for course_id in course_ids:
            item = await self.get_course(course_id)
            if item is not None:
                result.append(item)
        return result

    async def count_lessons_by_course(self, course_ids: list[str]) -> dict[str, int]:
        return {
            course_id: count
            for course_id in course_ids
            if (count := sum(item.course_id == course_id for item in self.lessons))
        }

    async def get_lesson(self, lesson_id: str) -> Lesson | None:
        return next((deepcopy(item) for item in self.lessons if item.id == lesson_id), None)

    async def list_lessons(self, course_ids: list[str] | None = None) -> list[Lesson]:
        return deepcopy(
            sorted(
                (item for item in self.lessons if course_ids is None or item.course_id in course_ids),
                key=lambda item: (item.course_id, item.position),
            )
        )


class MemoryPlans:
    def __init__(
        self,
        plans: list[StudyPlan],
        sessions: dict[str, StudySession] | None = None,
    ) -> None:
        self.plans = {item.id: deepcopy(item) for item in plans}
        self.goals: dict[str, Goal] = {}
        self.sessions = sessions if sessions is not None else {}

    async def get_plan(self, plan_id: str) -> StudyPlan | None:
        return deepcopy(self.plans.get(plan_id))

    async def list_plans(self) -> list[StudyPlan]:
        return deepcopy(sorted(self.plans.values(), key=lambda item: item.created_at))

    async def create_plan(
        self, *, name: str, weekly_minutes: int, start_date: date, course_ids: list[str]
    ) -> StudyPlan:
        plan = StudyPlan(
            str(uuid4()),
            name,
            weekly_minutes,
            start_date,
            list(course_ids),
            datetime.now(UTC).replace(tzinfo=None),
        )
        self.plans[plan.id] = deepcopy(plan)
        return plan

    async def update_plan_workload(self, plan_id: str, weekly_minutes: int) -> StudyPlan:
        if plan_id not in self.plans:
            raise NotFoundError("Unknown plan")
        self.plans[plan_id] = replace(self.plans[plan_id], weekly_minutes=weekly_minutes)
        return deepcopy(self.plans[plan_id])

    async def add_goal(self, *, plan_id: str, title: str, target_date: date, target_minutes: int) -> Goal:
        goal = Goal(str(uuid4()), plan_id, title, target_date, target_minutes, 0)
        self.goals[goal.id] = goal
        return deepcopy(goal)

    async def delete_plan(self, plan_id: str) -> None:
        if plan_id not in self.plans:
            raise NotFoundError("Unknown plan")
        del self.plans[plan_id]
        self.goals = {key: value for key, value in self.goals.items() if value.plan_id != plan_id}
        for session_id in [key for key, value in self.sessions.items() if value.plan_id == plan_id]:
            del self.sessions[session_id]

    async def delete_goal(self, plan_id: str, goal_id: str) -> None:
        goal = self.goals.get(goal_id)
        if goal is None or goal.plan_id != plan_id:
            raise NotFoundError("Unknown goal")
        del self.goals[goal_id]

    async def remove_course(self, plan_id: str, course_id: str, lesson_ids: list[str]) -> StudyPlan:
        plan = self.plans.get(plan_id)
        if plan is None:
            raise NotFoundError("Unknown plan")
        if course_id not in plan.course_ids:
            raise NotFoundError("Unknown plan course")
        if len(plan.course_ids) == 1:
            raise ConflictError("Cannot remove the last course")
        updated = replace(plan, course_ids=[item for item in plan.course_ids if item != course_id])
        self.plans[plan_id] = updated
        for session_id in [
            key
            for key, value in self.sessions.items()
            if value.plan_id == plan_id
            and value.lesson_id in lesson_ids
            and value.status == SessionStatus.PLANNED
        ]:
            del self.sessions[session_id]
        return deepcopy(updated)


class MemorySessions:
    def __init__(self, sessions: list[StudySession]) -> None:
        self.sessions = {item.id: deepcopy(item) for item in sessions}

    async def list_sessions(
        self, *, from_date: date | None = None, to_date: date | None = None
    ) -> list[StudySession]:
        return deepcopy(
            sorted(
                (
                    item
                    for item in self.sessions.values()
                    if (from_date is None or item.scheduled_for.date() >= from_date)
                    and (to_date is None or item.scheduled_for.date() <= to_date)
                ),
                key=lambda item: item.scheduled_for,
            )
        )

    async def list_plan_sessions(self, plan_id: str) -> list[StudySession]:
        return [item for item in await self.list_sessions() if item.plan_id == plan_id]

    async def get_session(self, session_id: str) -> StudySession | None:
        return deepcopy(self.sessions.get(session_id))

    async def create_session(
        self, *, plan_id: str, lesson_id: str, scheduled_for: datetime, duration_minutes: int
    ) -> StudySession:
        if scheduled_for.tzinfo:
            scheduled_for = scheduled_for.astimezone(UTC).replace(tzinfo=None)
        item = StudySession(
            str(uuid4()), plan_id, lesson_id, scheduled_for, duration_minutes, SessionStatus.PLANNED
        )
        self.sessions[item.id] = item
        return item

    async def save_session(self, session: StudySession) -> StudySession:
        await self.save_sessions([session])
        return deepcopy(self.sessions[session.id])

    async def save_sessions(self, sessions: list[StudySession]) -> None:
        if any(item.id not in self.sessions for item in sessions):
            raise NotFoundError("Unknown session")
        normalized = []
        for item in sessions:
            dates = {
                key: value.astimezone(UTC).replace(tzinfo=None) if value and value.tzinfo else value
                for key, value in [
                    ("scheduled_for", item.scheduled_for),
                    ("started_at", item.started_at),
                    ("completed_at", item.completed_at),
                ]
            }
            normalized.append(replace(item, **dates))
        self.sessions.update({item.id: deepcopy(item) for item in normalized})

    async def delete_session(self, session_id: str) -> None:
        session = self.sessions.get(session_id)
        if session is None:
            raise NotFoundError("Unknown session")
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError("Only planned sessions can be deleted")
        del self.sessions[session_id]


class MemoryPractice:
    def __init__(self, assignments: list[Assignment], answers: dict[str, str]) -> None:
        self.assignments = {item.id: deepcopy(item) for item in assignments}
        self.answers = dict(answers)
        self.attempts: list[Attempt] = []
        self.hints: set[str] = set()

    def _require(self, assignment_id: str) -> None:
        if assignment_id not in self.assignments:
            raise NotFoundError("Unknown assignment")

    async def get_assignment(self, assignment_id: str) -> Assignment | None:
        return deepcopy(self.assignments.get(assignment_id))

    async def list_assignments(self) -> list[Assignment]:
        return deepcopy(sorted(self.assignments.values(), key=lambda item: item.difficulty))

    async def list_attempts(self, assignment_id: str | None = None) -> list[Attempt]:
        return deepcopy(
            [item for item in self.attempts if assignment_id is None or item.assignment_id == assignment_id]
        )

    async def answer_for(self, assignment_id: str) -> str | None:
        return self.answers.get(assignment_id)

    async def mark_hint_requested(self, assignment_id: str) -> None:
        self._require(assignment_id)
        self.hints.add(assignment_id)

    async def clear_hint_marker(self, assignment_id: str) -> None:
        self._require(assignment_id)
        self.hints.discard(assignment_id)

    async def record_attempt(
        self, *, assignment_id: str, answer: str, evaluation: AnswerEvaluation
    ) -> Attempt:
        self._require(assignment_id)
        hinted = assignment_id in self.hints
        item = Attempt(
            str(uuid4()),
            assignment_id,
            answer,
            evaluation.is_correct,
            evaluation.hinted_score if hinted else evaluation.score,
            hinted,
            datetime.now(UTC).replace(tzinfo=None),
        )
        self.attempts.append(item)
        self.hints.discard(assignment_id)
        return item
