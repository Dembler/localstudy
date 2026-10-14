from dataclasses import dataclass, field
from datetime import date, datetime
from enum import StrEnum


class CourseLevel(StrEnum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"


class SessionStatus(StrEnum):
    PLANNED = "planned"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"


@dataclass(slots=True, frozen=True)
class Course:
    id: str
    slug: str
    title: str
    description: str
    level: CourseLevel
    duration_minutes: int
    skills: list[str] = field(default_factory=list)
    prerequisite_ids: list[str] = field(default_factory=list)


@dataclass(slots=True, frozen=True)
class Lesson:
    id: str
    course_id: str
    title: str
    summary: str
    preview: str
    duration_minutes: int
    position: int


@dataclass(slots=True, frozen=True)
class StudyPlan:
    id: str
    name: str
    weekly_minutes: int
    start_date: date
    course_ids: list[str]
    created_at: datetime


@dataclass(slots=True, frozen=True)
class Goal:
    id: str
    plan_id: str
    title: str
    target_date: date
    target_minutes: int
    progress_percent: int


@dataclass(slots=True, frozen=True)
class StudySession:
    id: str
    plan_id: str
    lesson_id: str
    scheduled_for: datetime
    duration_minutes: int
    status: SessionStatus
    started_at: datetime | None = None
    completed_at: datetime | None = None
    score: int | None = None


@dataclass(slots=True, frozen=True)
class Assignment:
    id: str
    lesson_id: str
    topic: str
    prompt: str
    hint: str
    difficulty: int


@dataclass(slots=True, frozen=True)
class Attempt:
    id: str
    assignment_id: str
    answer: str
    is_correct: bool
    score: int
    hint_used: bool
    created_at: datetime


@dataclass(slots=True, frozen=True)
class AnswerEvaluation:
    is_correct: bool
    score: int
    hinted_score: int
