from datetime import date, datetime

from pydantic import BaseModel, Field

from src.domain.entities import CourseLevel, SessionStatus


class CourseSummary(BaseModel):
    id: str
    slug: str
    title: str
    description: str
    level: CourseLevel
    duration_minutes: int
    skills: list[str]
    lesson_count: int = Field(ge=0)


class CourseDetail(CourseSummary):
    prerequisite_ids: list[str]


class CourseList(BaseModel):
    items: list[CourseSummary]
    total: int


class LessonPreview(BaseModel):
    id: str
    course_id: str
    title: str
    summary: str
    preview: str
    duration_minutes: int
    position: int


class PlanView(BaseModel):
    id: str
    name: str
    weekly_minutes: int
    start_date: date
    course_ids: list[str]
    created_at: datetime


class GoalView(BaseModel):
    id: str
    plan_id: str
    title: str
    target_date: date
    target_minutes: int
    progress_percent: int


class RebalanceResult(BaseModel):
    plan_id: str
    sessions_updated: int
    weekly_minutes: int
    message: str


class ForecastView(BaseModel):
    plan_id: str
    remaining_minutes: int
    weekly_minutes: int
    expected_completion: date
    weeks_remaining: int
    confidence: str


class SessionView(BaseModel):
    id: str
    plan_id: str
    lesson_id: str
    lesson_title: str
    scheduled_for: datetime
    duration_minutes: int
    status: SessionStatus
    started_at: datetime | None
    completed_at: datetime | None
    score: int | None


class SessionCalendar(BaseModel):
    items: list[SessionView]
    total: int
    from_date: date
    to_date: date


class AssignmentView(BaseModel):
    id: str
    lesson_id: str
    topic: str
    prompt: str
    difficulty: int
    attempts_count: int


class AttemptView(BaseModel):
    id: str
    assignment_id: str
    answer: str
    is_correct: bool
    score: int
    hint_used: bool
    created_at: datetime


class HintView(BaseModel):
    assignment_id: str
    hint: str
    penalty_percent: int


class RetryView(BaseModel):
    assignment: AssignmentView
    previous_best_score: int
    message: str


class AttemptHistory(BaseModel):
    items: list[AttemptView]
    total: int
    best_score: int


class OverviewAnalytics(BaseModel):
    courses_in_plan: int
    completed_sessions: int
    study_minutes: int
    average_score: int
    completion_percent: int


class SkillProgress(BaseModel):
    skill: str
    progress_percent: int
    level: str


class SkillsAnalytics(BaseModel):
    items: list[SkillProgress]


class StreakAnalytics(BaseModel):
    current_days: int
    longest_days: int
    last_study_date: date | None


class WeakTopic(BaseModel):
    topic: str
    average_score: int
    attempts: int
    suggested_action: str


class WeakTopicsAnalytics(BaseModel):
    items: list[WeakTopic]


class Recommendation(BaseModel):
    kind: str
    title: str
    reason: str
    action_id: str | None = None


class RecommendationsAnalytics(BaseModel):
    items: list[Recommendation]
