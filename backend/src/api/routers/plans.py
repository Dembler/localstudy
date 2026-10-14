from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, status

from src.api.schemas import AddGoalRequest, ApiResponse, CreatePlanRequest, UpdateWorkloadRequest
from src.application.schemas import ForecastView, GoalView, PlanView, RebalanceResult
from src.application.services import PlanService

router = APIRouter(route_class=DishkaRoute, prefix="/plans", tags=["study plans"])
PlanId = Annotated[str, Path(min_length=2, max_length=80)]


@router.post("", response_model=ApiResponse[PlanView], status_code=status.HTTP_201_CREATED)
async def create_plan(payload: CreatePlanRequest, service: FromDishka[PlanService]) -> ApiResponse[PlanView]:
    return ApiResponse(data=await service.create_plan(**payload.model_dump()))


@router.patch("/{plan_id}/workload", response_model=ApiResponse[PlanView])
async def update_workload(
    plan_id: PlanId,
    payload: UpdateWorkloadRequest,
    service: FromDishka[PlanService],
) -> ApiResponse[PlanView]:
    return ApiResponse(data=await service.update_workload(plan_id, payload.weekly_minutes))


@router.post("/{plan_id}/goals", response_model=ApiResponse[GoalView], status_code=status.HTTP_201_CREATED)
async def add_goal(
    plan_id: PlanId,
    payload: AddGoalRequest,
    service: FromDishka[PlanService],
) -> ApiResponse[GoalView]:
    return ApiResponse(data=await service.add_goal(plan_id=plan_id, **payload.model_dump()))


@router.post("/{plan_id}/rebalance", response_model=ApiResponse[RebalanceResult])
async def rebalance_plan(plan_id: PlanId, service: FromDishka[PlanService]) -> ApiResponse[RebalanceResult]:
    return ApiResponse(data=await service.rebalance(plan_id))


@router.get("/{plan_id}/forecast", response_model=ApiResponse[ForecastView])
async def forecast_plan(plan_id: PlanId, service: FromDishka[PlanService]) -> ApiResponse[ForecastView]:
    return ApiResponse(data=await service.forecast(plan_id))


@router.delete("/{plan_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_plan(plan_id: PlanId, service: FromDishka[PlanService]) -> None:
    await service.delete_plan(plan_id)


@router.delete("/{plan_id}/goals/{goal_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_goal(
    plan_id: PlanId,
    goal_id: Annotated[str, Path(min_length=2, max_length=80)],
    service: FromDishka[PlanService],
) -> None:
    await service.delete_goal(plan_id, goal_id)


@router.delete("/{plan_id}/courses/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_course(
    plan_id: PlanId,
    course_id: Annotated[str, Path(min_length=2, max_length=80)],
    service: FromDishka[PlanService],
) -> None:
    await service.remove_course(plan_id, course_id)
