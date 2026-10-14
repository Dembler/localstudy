from collections import defaultdict
from dataclasses import replace
from datetime import timedelta

from src.application.policies.practice import AssignmentSelector
from src.application.policies.recommendations import RecommendationContext, RecommendationPolicy
from src.application.ports import CatalogReader, Clock, PlanReader, PracticeReader, SessionReader
from src.application.schemas import (
    OverviewAnalytics,
    RecommendationsAnalytics,
    SkillProgress,
    SkillsAnalytics,
    StreakAnalytics,
    WeakTopic,
    WeakTopicsAnalytics,
)
from src.domain.entities import SessionStatus


class AnalyticsService:
    def __init__(
        self,
        plans: PlanReader,
        catalog: CatalogReader,
        sessions: SessionReader,
        practice: PracticeReader,
        recommendations: RecommendationPolicy,
        selector: AssignmentSelector,
        clock: Clock,
    ) -> None:
        self._plans = plans
        self._catalog = catalog
        self._sessions = sessions
        self._practice = practice
        self._recommendations = recommendations
        self._selector = selector
        self._clock = clock

    async def analytics_overview(self) -> OverviewAnalytics:
        plans = await self._plans.list_plans()
        sessions = await self._sessions.list_sessions()
        completed = [item for item in sessions if item.status == SessionStatus.COMPLETED]
        scores = [item.score for item in completed if item.score is not None]
        course_ids = {course_id for plan in plans for course_id in plan.course_ids}
        lessons = await self._catalog.list_lessons(list(course_ids)) if course_ids else []
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
        courses = await self._catalog.list_courses()
        lessons = await self._catalog.list_lessons()
        completed = {
            item.lesson_id
            for item in await self._sessions.list_sessions()
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
                for item in await self._sessions.list_sessions()
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
        if completed_dates[-1] < self._clock.today() - timedelta(days=1):
            current_days = 0
        return StreakAnalytics(
            current_days=current_days,
            longest_days=longest,
            last_study_date=completed_dates[-1],
        )

    async def analytics_weak_topics(self) -> WeakTopicsAnalytics:
        attempts = await self._practice.list_attempts()
        assignments = {item.id: item for item in await self._practice.list_assignments()}
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
        weak = await self.analytics_weak_topics()
        planned = [
            item for item in await self._sessions.list_sessions() if item.status == SessionStatus.PLANNED
        ]
        lessons = {item.id: item for item in await self._catalog.list_lessons()} if planned else {}
        context = RecommendationContext(weak.items, planned, lessons)
        items = self._recommendations.recommend(context)
        if not items:
            assignment = self._selector.select(
                await self._practice.list_assignments(), await self._practice.list_attempts()
            )
            items = self._recommendations.recommend(replace(context, fallback_assignment_id=assignment.id))
        return RecommendationsAnalytics(items=items)
