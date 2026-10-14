from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, Query, status

from src.application.schemas import (
    ApiResponse,
    AssignmentView,
    AttemptHistory,
    AttemptRequest,
    AttemptView,
    HintView,
    RetryView,
)
from src.application.services import LearningService

router = APIRouter(route_class=DishkaRoute, prefix="/practice", tags=["practice"])
AssignmentId = Annotated[str, Path(min_length=2, max_length=80)]


@router.get("/next", response_model=ApiResponse[AssignmentView])
async def next_assignment(
    service: FromDishka[LearningService],
    plan_id: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
    course_id: Annotated[str | None, Query(min_length=2, max_length=80)] = None,
) -> ApiResponse[AssignmentView]:
    return ApiResponse(data=await service.next_assignment(plan_id=plan_id, course_id=course_id))


@router.post(
    "/assignments/{assignment_id}/attempts",
    response_model=ApiResponse[AttemptView],
    status_code=status.HTTP_201_CREATED,
)
async def submit_attempt(
    assignment_id: AssignmentId,
    payload: AttemptRequest,
    service: FromDishka[LearningService],
) -> ApiResponse[AttemptView]:
    return ApiResponse(data=await service.submit_attempt(assignment_id, payload.answer))


@router.post("/assignments/{assignment_id}/hint", response_model=ApiResponse[HintView])
async def get_hint(
    assignment_id: AssignmentId, service: FromDishka[LearningService]
) -> ApiResponse[HintView]:
    return ApiResponse(data=await service.hint(assignment_id))


@router.post("/assignments/{assignment_id}/retry", response_model=ApiResponse[RetryView])
async def retry_assignment(
    assignment_id: AssignmentId, service: FromDishka[LearningService]
) -> ApiResponse[RetryView]:
    return ApiResponse(data=await service.retry(assignment_id))


@router.get("/assignments/{assignment_id}/attempts", response_model=ApiResponse[AttemptHistory])
async def get_attempts(
    assignment_id: AssignmentId, service: FromDishka[LearningService]
) -> ApiResponse[AttemptHistory]:
    return ApiResponse(data=await service.attempt_history(assignment_id))
