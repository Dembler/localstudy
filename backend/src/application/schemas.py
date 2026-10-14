from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field

from src.domain.entities import CourseLevel, SessionStatus

T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    status: str = "success"
    data: T


class ErrorBody(BaseModel):
    code: str
    message: str
    details: Any = Field(default_factory=dict)
    request_id: str


class ErrorResponse(BaseModel):
    status: str = "error"
    error: ErrorBody


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


class CreatePlanRequest(BaseModel):
    name: str = Field(min_length=2, max_length=80)
    weekly_minutes: int = Field(ge=60, le=2400)
    start_date: date = Field(default_factory=date.today)
    course_ids: list[str] = Field(min_length=1, max_length=10)


class UpdateWorkloadRequest(BaseModel):
    weekly_minutes: int = Field(ge=60, le=2400)


class AddGoalRequest(BaseModel):
    title: str = Field(min_length=2, max_length=120)
    target_date: date
    target_minutes: int = Field(ge=30, le=100_000)


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


class CreateSessionRequest(BaseModel):
    plan_id: str
    lesson_id: str
    scheduled_for: datetime
    duration_minutes: int = Field(ge=10, le=480)


class RescheduleSessionRequest(BaseModel):
    scheduled_for: datetime


class CompleteSessionRequest(BaseModel):
    score: int | None = Field(default=None, ge=0, le=100)


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


class AttemptRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)


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


class ORMBaseModel(BaseModel):
    model_config = ConfigDict(from_attributes=True)
