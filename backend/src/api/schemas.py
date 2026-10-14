from datetime import date, datetime
from typing import Any, Generic, TypeVar

from pydantic import BaseModel, Field

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


class CreateSessionRequest(BaseModel):
    plan_id: str
    lesson_id: str
    scheduled_for: datetime
    duration_minutes: int = Field(ge=10, le=480)


class RescheduleSessionRequest(BaseModel):
    scheduled_for: datetime


class CompleteSessionRequest(BaseModel):
    score: int | None = Field(default=None, ge=0, le=100)


class AttemptRequest(BaseModel):
    answer: str = Field(min_length=1, max_length=2000)
