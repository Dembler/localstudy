import logging
import math
from collections import defaultdict
from dataclasses import replace
from datetime import UTC, date, datetime, timedelta
from http import HTTPStatus

from src.application.ports import LearningRepository
from src.application.schemas import (
    AssignmentView,
    AttemptHistory,
    AttemptView,
    CourseDetail,
    CourseList,
    CourseSummary,
    ForecastView,
    GoalView,
    HintView,
    LessonPreview,
    OverviewAnalytics,
    PlanView,
    RebalanceResult,
    Recommendation,
    RecommendationsAnalytics,
    RetryView,
    SessionCalendar,
    SessionView,
    SkillProgress,
    SkillsAnalytics,
    StreakAnalytics,
    WeakTopic,
    WeakTopicsAnalytics,
)
from src.domain.entities import (
    Assignment,
    Attempt,
    Course,
    Lesson,
    SessionStatus,
    StudyPlan,
    StudySession,
)
from src.domain.exceptions import ConflictError, InvalidStateError, NotFoundError, ValidationError


class LearningService:
    def __init__(self, repository: LearningRepository, logger: logging.Logger) -> None:
        self._repository = repository
        self._logger = logger

    async def list_courses(self, level: str | None, skill: str | None) -> CourseList:
        courses = await self._repository.list_courses(level=level, skill=skill)
        return CourseList(items=await self._course_summaries(courses), total=len(courses))

    async def search_courses(self, query: str) -> CourseList:
        courses = await self._repository.search_courses(query)
        return CourseList(items=await self._course_summaries(courses), total=len(courses))

    async def get_course(self, course_id: str) -> CourseDetail:
        course = await self._require_course(course_id)
        summary = (await self._course_summaries([course]))[0]
        return CourseDetail(
            **summary.model_dump(),
            prerequisite_ids=course.prerequisite_ids,
        )

    async def prerequisites(self, course_id: str) -> CourseList:
        course = await self._require_course(course_id)
        direct_prerequisites = await self._repository.get_courses(course.prerequisite_ids)
        prerequisite_ids = await self._expand_prerequisites(direct_prerequisites)
        prerequisites = await self._repository.get_courses(prerequisite_ids)
        return CourseList(items=await self._course_summaries(prerequisites), total=len(prerequisites))

    async def lesson_preview(self, lesson_id: str) -> LessonPreview:
        lesson = await self._repository.get_lesson(lesson_id)
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

    async def create_plan(
        self, *, name: str, weekly_minutes: int, start_date: date, course_ids: list[str]
    ) -> PlanView:
        unique_ids = list(dict.fromkeys(course_ids))
        courses = await self._repository.get_courses(unique_ids)
        if len(courses) != len(unique_ids):
            found = {course.id for course in courses}
            raise NotFoundError(
                "Один или несколько курсов не найдены",
                details={"missing_course_ids": [item for item in unique_ids if item not in found]},
            )
        expanded = await self._expand_prerequisites(courses)
        plan = await self._repository.create_plan(
            name=name,
            weekly_minutes=weekly_minutes,
            start_date=start_date,
            course_ids=expanded,
        )
        self._logger.info("study plan created", extra={"plan_id": plan.id})
        return self._plan_view(plan)

    async def update_workload(self, plan_id: str, weekly_minutes: int) -> PlanView:
        await self._require_plan(plan_id)
        plan = await self._repository.update_plan_workload(plan_id, weekly_minutes)
        return self._plan_view(plan)

    async def add_goal(self, *, plan_id: str, title: str, target_date: date, target_minutes: int) -> GoalView:
        await self._require_plan(plan_id)
        if target_date < date.today():
            raise ValidationError("Дата цели не может быть в прошлом")
        goal = await self._repository.add_goal(
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

    async def rebalance(self, plan_id: str) -> RebalanceResult:
        plan = await self._require_plan(plan_id)
        changed = await self._repository.rebalance_plan_sessions(plan)
        return RebalanceResult(
            plan_id=plan.id,
            sessions_updated=changed,
            weekly_minutes=plan.weekly_minutes,
            message="Запланированные занятия распределены по доступным учебным дням",
        )

    async def forecast(self, plan_id: str) -> ForecastView:
        plan = await self._require_plan(plan_id)
        lessons = await self._repository.list_lessons(plan.course_ids)
        sessions = await self._repository.list_plan_sessions(plan.id)
        completed_lesson_ids = {
            session.lesson_id for session in sessions if session.status == SessionStatus.COMPLETED
        }
        completed_minutes = sum(
            lesson.duration_minutes for lesson in lessons if lesson.id in completed_lesson_ids
        )
        remaining = max(0, sum(item.duration_minutes for item in lessons) - completed_minutes)
        weeks = math.ceil(remaining / plan.weekly_minutes) if remaining else 0
        expected = date.today() + timedelta(weeks=weeks)
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

    async def calendar(self, from_date: date, to_date: date) -> SessionCalendar:
        if to_date < from_date:
            raise ValidationError("Конечная дата должна быть не раньше начальной")
        sessions = await self._repository.list_sessions(from_date=from_date, to_date=to_date)
        items = [await self._session_view(item) for item in sessions]
        return SessionCalendar(items=items, total=len(items), from_date=from_date, to_date=to_date)

    async def create_session(
        self,
        *,
        plan_id: str,
        lesson_id: str,
        scheduled_for: datetime,
        duration_minutes: int,
    ) -> SessionView:
        plan = await self._require_plan(plan_id)
        lesson = await self._require_lesson(lesson_id)
        if lesson.course_id not in plan.course_ids:
            raise ConflictError("Урок не относится к курсу из этого учебного плана")
        session = await self._repository.create_session(
            plan_id=plan_id,
            lesson_id=lesson_id,
            scheduled_for=scheduled_for,
            duration_minutes=duration_minutes,
        )
        return await self._session_view(session)

    async def start_session(self, session_id: str) -> SessionView:
        session = await self._require_session(session_id)
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError(
                "Начать можно только запланированное занятие", details={"status": session.status}
            )
        updated = replace(
            session,
            status=SessionStatus.IN_PROGRESS,
            started_at=self._now(),
        )
        return await self._session_view(await self._repository.save_session(updated))

    async def complete_session(self, session_id: str, score: int | None) -> SessionView:
        session = await self._require_session(session_id)
        if session.status != SessionStatus.IN_PROGRESS:
            raise InvalidStateError(
                "Завершить можно только начатое занятие", details={"status": session.status}
            )
        updated = replace(
            session,
            status=SessionStatus.COMPLETED,
            completed_at=self._now(),
            score=score,
        )
        return await self._session_view(await self._repository.save_session(updated))

    async def reschedule_session(self, session_id: str, scheduled_for: datetime) -> SessionView:
        session = await self._require_session(session_id)
        if session.status != SessionStatus.PLANNED:
            raise InvalidStateError("Перенести можно только запланированное занятие")
        updated = replace(session, scheduled_for=scheduled_for)
        return await self._session_view(await self._repository.save_session(updated))

    async def next_assignment(
        self, *, plan_id: str | None = None, course_id: str | None = None
    ) -> AssignmentView:
        if course_id is not None and plan_id is None:
            raise ValidationError("Курс можно уточнить только вместе с учебным планом")
        assignments = await self._repository.list_assignments()
        if plan_id is not None:
            plan = await self._require_plan(plan_id)
            if course_id is not None and course_id not in plan.course_ids:
                raise ConflictError(
                    "Курс не относится к этому учебному плану",
                    details={"plan_id": plan_id, "course_id": course_id},
                )
            course_ids = [course_id] if course_id is not None else plan.course_ids
            lesson_ids = {item.id for item in await self._repository.list_lessons(course_ids)}
            assignments = [item for item in assignments if item.lesson_id in lesson_ids]
        if not assignments:
            raise NotFoundError("Нет доступных практических заданий")
        attempts = await self._repository.list_attempts()
        grouped: dict[str, list[Attempt]] = defaultdict(list)
        for attempt in attempts:
            grouped[attempt.assignment_id].append(attempt)
        assignment = min(
            assignments,
            key=lambda item: (
                max((attempt.score for attempt in grouped[item.id]), default=-1),
                len(grouped[item.id]),
                item.difficulty,
            ),
        )
        return self._assignment_view(assignment, len(grouped[assignment.id]))

    async def submit_attempt(self, assignment_id: str, answer: str) -> AttemptView:
        await self._require_assignment(assignment_id)
        expected = await self._repository.answer_for(assignment_id)
        if expected is None:
            raise NotFoundError("Задание не найдено")
        normalized = " ".join(answer.casefold().split())
        normalized_expected = " ".join(expected.casefold().split())
        accepted_answers = {normalized_expected}
        if normalized_expected.isdecimal():
            try:
                status_phrase = HTTPStatus(int(normalized_expected)).phrase.casefold()
                accepted_answers.add(f"{normalized_expected} {status_phrase}")
            except ValueError:
                pass
        is_correct = normalized in accepted_answers
        hint_used = await self._repository.consume_hint_marker(assignment_id)
        score = (100 if is_correct else 35) - (15 if hint_used else 0)
        attempt = await self._repository.create_attempt(
            assignment_id=assignment_id,
            answer=answer,
            is_correct=is_correct,
            score=max(0, score),
            hint_used=hint_used,
        )
        return self._attempt_view(attempt)

    async def hint(self, assignment_id: str) -> HintView:
        assignment = await self._require_assignment(assignment_id)
        await self._repository.mark_hint_requested(assignment_id)
        return HintView(assignment_id=assignment.id, hint=assignment.hint, penalty_percent=15)

    async def retry(self, assignment_id: str) -> RetryView:
        assignment = await self._require_assignment(assignment_id)
        attempts = await self._repository.list_attempts(assignment_id)
        if not attempts:
            raise ConflictError("Перед повторной попыткой отправьте первый ответ")
        await self._repository.clear_hint_marker(assignment_id)
        return RetryView(
            assignment=self._assignment_view(assignment, len(attempts)),
            previous_best_score=max(item.score for item in attempts),
            message="Повторная попытка готова: подсказка сброшена",
        )

    async def attempt_history(self, assignment_id: str) -> AttemptHistory:
        await self._require_assignment(assignment_id)
        attempts = await self._repository.list_attempts(assignment_id)
        return AttemptHistory(
            items=[self._attempt_view(item) for item in attempts],
            total=len(attempts),
            best_score=max((item.score for item in attempts), default=0),
        )

    async def analytics_overview(self) -> OverviewAnalytics:
        plans = await self._repository.list_plans()
        sessions = await self._repository.list_sessions()
        completed = [item for item in sessions if item.status == SessionStatus.COMPLETED]
        scores = [item.score for item in completed if item.score is not None]
        course_ids = {course_id for plan in plans for course_id in plan.course_ids}
        lessons = await self._repository.list_lessons(list(course_ids)) if course_ids else []
        total_minutes = sum(item.duration_minutes for item in lessons)
        studied = sum(item.duration_minutes for item in completed)
        completed_lesson_ids = {item.lesson_id for item in completed}
        completed_curriculum_minutes = sum(
            lesson.duration_minutes for lesson in lessons if lesson.id in completed_lesson_ids
        )
        return OverviewAnalytics(
            courses_in_plan=len(course_ids),
            completed_sessions=len(completed),
            study_minutes=studied,
            average_score=round(sum(scores) / len(scores)) if scores else 0,
            completion_percent=(
                round(completed_curriculum_minutes / total_minutes * 100) if total_minutes else 0
            ),
        )

    async def analytics_skills(self) -> SkillsAnalytics:
        courses = await self._repository.list_courses()
        lessons = await self._repository.list_lessons()
        completed = {
            item.lesson_id
            for item in await self._repository.list_sessions()
            if item.status == SessionStatus.COMPLETED
        }
        lessons_by_course: dict[str, list[str]] = defaultdict(list)
        for lesson in lessons:
            lessons_by_course[lesson.course_id].append(lesson.id)
        skill_scores: dict[str, list[int]] = defaultdict(list)
        for course in courses:
            course_lessons = lessons_by_course[course.id]
            progress = (
                round(sum(item in completed for item in course_lessons) / len(course_lessons) * 100)
                if course_lessons
                else 0
            )
            for skill in course.skills:
                skill_scores[skill].append(progress)
        items = []
        for skill, values in sorted(skill_scores.items()):
            progress = round(sum(values) / len(values))
            level = "strong" if progress >= 75 else "developing" if progress >= 35 else "new"
            items.append(SkillProgress(skill=skill, progress_percent=progress, level=level))
        return SkillsAnalytics(items=items)

    async def analytics_streak(self) -> StreakAnalytics:
        completed_dates = sorted(
            {
                (item.completed_at or item.scheduled_for).date()
                for item in await self._repository.list_sessions()
                if item.status == SessionStatus.COMPLETED
            }
        )
        if not completed_dates:
            return StreakAnalytics(current_days=0, longest_days=0, last_study_date=None)
        longest = current_run = 1
        for previous, current_date in zip(completed_dates, completed_dates[1:], strict=False):
            current_run = current_run + 1 if current_date - previous == timedelta(days=1) else 1
            longest = max(longest, current_run)
        current_days = 1
        cursor = completed_dates[-1]
        completed_set = set(completed_dates)
        while cursor - timedelta(days=1) in completed_set:
            current_days += 1
            cursor -= timedelta(days=1)
        if completed_dates[-1] < date.today() - timedelta(days=1):
            current_days = 0
        return StreakAnalytics(
            current_days=current_days,
            longest_days=longest,
            last_study_date=completed_dates[-1],
        )

    async def analytics_weak_topics(self) -> WeakTopicsAnalytics:
        attempts = await self._repository.list_attempts()
        assignments = {item.id: item for item in await self._repository.list_assignments()}
        by_topic: dict[str, list[int]] = defaultdict(list)
        for attempt in attempts:
            assignment = assignments.get(attempt.assignment_id)
            if assignment:
                by_topic[assignment.topic].append(attempt.score)
        weak = []
        for topic, scores in by_topic.items():
            average = round(sum(scores) / len(scores))
            if average < 80:
                weak.append(
                    WeakTopic(
                        topic=topic,
                        average_score=average,
                        attempts=len(scores),
                        suggested_action="Повторите материал урока и выполните задание ещё раз",
                    )
                )
        weak.sort(key=lambda item: item.average_score)
        return WeakTopicsAnalytics(items=weak)

    async def analytics_recommendations(self) -> RecommendationsAnalytics:
        items: list[Recommendation] = []
        weak = await self.analytics_weak_topics()
        for topic in weak.items[:2]:
            items.append(
                Recommendation(
                    kind="practice",
                    title=f"Закрепить тему «{topic.topic}»",
                    reason=f"Текущий средний результат — {topic.average_score}%",
                )
            )
        planned = [
            item for item in await self._repository.list_sessions() if item.status == SessionStatus.PLANNED
        ]
        if planned:
            upcoming = min(planned, key=lambda item: item.scheduled_for)
            lesson = await self._repository.get_lesson(upcoming.lesson_id)
            items.append(
                Recommendation(
                    kind="schedule",
                    title=f"Подготовиться к занятию «{lesson.title if lesson else 'Следующий урок'}»",
                    reason="Это ближайшее запланированное занятие",
                    action_id=upcoming.id,
                )
            )
        if not items:
            assignment = await self.next_assignment()
            items.append(
                Recommendation(
                    kind="practice",
                    title="Сохранить темп обучения",
                    reason="Доступно короткое практическое задание",
                    action_id=assignment.id,
                )
            )
        return RecommendationsAnalytics(items=items)

    async def _expand_prerequisites(self, courses: list[Course]) -> list[str]:
        result: list[str] = []
        visiting: set[str] = set()

        async def add(course: Course) -> None:
            if course.id in visiting:
                raise ConflictError("Обнаружен цикл зависимостей между курсами")
            if course.id in result:
                return
            visiting.add(course.id)
            for prerequisite_id in course.prerequisite_ids:
                prerequisite = await self._require_course(prerequisite_id)
                await add(prerequisite)
            visiting.remove(course.id)
            result.append(course.id)

        for course in courses:
            await add(course)
        return result

    async def _require_course(self, course_id: str) -> Course:
        course = await self._repository.get_course(course_id)
        if course is None:
            raise NotFoundError("Курс не найден", details={"course_id": course_id})
        return course

    async def _require_lesson(self, lesson_id: str) -> Lesson:
        lesson = await self._repository.get_lesson(lesson_id)
        if lesson is None:
            raise NotFoundError("Урок не найден", details={"lesson_id": lesson_id})
        return lesson

    async def _require_plan(self, plan_id: str) -> StudyPlan:
        plan = await self._repository.get_plan(plan_id)
        if plan is None:
            raise NotFoundError("Учебный план не найден", details={"plan_id": plan_id})
        return plan

    async def _require_session(self, session_id: str) -> StudySession:
        session = await self._repository.get_session(session_id)
        if session is None:
            raise NotFoundError("Учебное занятие не найдено", details={"session_id": session_id})
        return session

    async def _require_assignment(self, assignment_id: str) -> Assignment:
        assignment = await self._repository.get_assignment(assignment_id)
        if assignment is None:
            raise NotFoundError("Задание не найдено", details={"assignment_id": assignment_id})
        return assignment

    async def _session_view(self, session: StudySession) -> SessionView:
        lesson = await self._repository.get_lesson(session.lesson_id)
        return SessionView(
            **self._session_values(session),
            lesson_title=lesson.title if lesson else "Неизвестный урок",
        )

    async def _course_summaries(self, courses: list[Course]) -> list[CourseSummary]:
        lesson_counts = await self._repository.count_lessons_by_course([course.id for course in courses])
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

    @staticmethod
    def _session_values(session: StudySession) -> dict[str, object]:
        return {
            "id": session.id,
            "plan_id": session.plan_id,
            "lesson_id": session.lesson_id,
            "scheduled_for": session.scheduled_for,
            "duration_minutes": session.duration_minutes,
            "status": session.status,
            "started_at": session.started_at,
            "completed_at": session.completed_at,
            "score": session.score,
        }

    @staticmethod
    def _assignment_view(assignment: Assignment, attempts_count: int) -> AssignmentView:
        return AssignmentView(
            id=assignment.id,
            lesson_id=assignment.lesson_id,
            topic=assignment.topic,
            prompt=assignment.prompt,
            difficulty=assignment.difficulty,
            attempts_count=attempts_count,
        )

    @staticmethod
    def _attempt_view(attempt: Attempt) -> AttemptView:
        return AttemptView(
            id=attempt.id,
            assignment_id=attempt.assignment_id,
            answer=attempt.answer,
            is_correct=attempt.is_correct,
            score=attempt.score,
            hint_used=attempt.hint_used,
            created_at=attempt.created_at,
        )

    @staticmethod
    def _now() -> datetime:
        return datetime.now(UTC).replace(tzinfo=None)
