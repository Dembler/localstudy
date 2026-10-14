from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, status

from src.application.schemas import (
    AddGoalRequest,
    ApiResponse,
    CreatePlanRequest,
    ForecastView,
    GoalView,
    PlanView,
    RebalanceResult,
    UpdateWorkloadRequest,
)
from src.application.services import LearningService

router = APIRouter(route_class=DishkaRoute, prefix="/plans", tags=["study plans"])
PlanId = Annotated[str, Path(min_length=2, max_length=80)]


@router.post("", response_model=ApiResponse[PlanView], status_code=status.HTTP_201_CREATED)
async def create_plan(
    payload: CreatePlanRequest, service: FromDishka[LearningService]
) -> ApiResponse[PlanView]:
    return ApiResponse(data=await service.create_plan(**payload.model_dump()))


@router.patch("/{plan_id}/workload", response_model=ApiResponse[PlanView])
async def update_workload(
    plan_id: PlanId,
    payload: UpdateWorkloadRequest,
    service: FromDishka[LearningService],
) -> ApiResponse[PlanView]:
    return ApiResponse(data=await service.update_workload(plan_id, payload.weekly_minutes))


@router.post("/{plan_id}/goals", response_model=ApiResponse[GoalView], status_code=status.HTTP_201_CREATED)
async def add_goal(
    plan_id: PlanId,
    payload: AddGoalRequest,
    service: FromDishka[LearningService],
) -> ApiResponse[GoalView]:
    return ApiResponse(data=await service.add_goal(plan_id=plan_id, **payload.model_dump()))


@router.post("/{plan_id}/rebalance", response_model=ApiResponse[RebalanceResult])
async def rebalance_plan(
    plan_id: PlanId, service: FromDishka[LearningService]
) -> ApiResponse[RebalanceResult]:
    return ApiResponse(data=await service.rebalance(plan_id))


@router.get("/{plan_id}/forecast", response_model=ApiResponse[ForecastView])
async def forecast_plan(plan_id: PlanId, service: FromDishka[LearningService]) -> ApiResponse[ForecastView]:
    return ApiResponse(data=await service.forecast(plan_id))
