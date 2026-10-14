from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter

from src.application.schemas import (
    ApiResponse,
    OverviewAnalytics,
    RecommendationsAnalytics,
    SkillsAnalytics,
    StreakAnalytics,
    WeakTopicsAnalytics,
)
from src.application.services import LearningService

router = APIRouter(route_class=DishkaRoute, prefix="/analytics", tags=["analytics"])


@router.get("/overview", response_model=ApiResponse[OverviewAnalytics])
async def overview(service: FromDishka[LearningService]) -> ApiResponse[OverviewAnalytics]:
    return ApiResponse(data=await service.analytics_overview())


@router.get("/skills", response_model=ApiResponse[SkillsAnalytics])
async def skills(service: FromDishka[LearningService]) -> ApiResponse[SkillsAnalytics]:
    return ApiResponse(data=await service.analytics_skills())


@router.get("/streak", response_model=ApiResponse[StreakAnalytics])
async def streak(service: FromDishka[LearningService]) -> ApiResponse[StreakAnalytics]:
    return ApiResponse(data=await service.analytics_streak())


@router.get("/weak-topics", response_model=ApiResponse[WeakTopicsAnalytics])
async def weak_topics(service: FromDishka[LearningService]) -> ApiResponse[WeakTopicsAnalytics]:
    return ApiResponse(data=await service.analytics_weak_topics())


@router.get("/recommendations", response_model=ApiResponse[RecommendationsAnalytics])
async def recommendations(
    service: FromDishka[LearningService],
) -> ApiResponse[RecommendationsAnalytics]:
    return ApiResponse(data=await service.analytics_recommendations())
