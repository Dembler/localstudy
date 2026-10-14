from typing import Any

from fastapi import APIRouter

from src.api.routers.analytics import router as analytics_router
from src.api.routers.courses import router as courses_router
from src.api.routers.plans import router as plans_router
from src.api.routers.practice import router as practice_router
from src.api.routers.sessions import router as sessions_router
from src.application.schemas import ErrorResponse

api_router = APIRouter()
ERROR_RESPONSES: dict[int | str, dict[str, Any]] = {
    404: {"model": ErrorResponse, "description": "Ресурс или маршрут не найден"},
    409: {"model": ErrorResponse, "description": "Конфликт бизнес-состояния"},
    422: {"model": ErrorResponse, "description": "Ошибка проверки запроса"},
    500: {"model": ErrorResponse, "description": "Непредвиденная ошибка сервера"},
}

api_router.include_router(courses_router, responses=ERROR_RESPONSES)
api_router.include_router(plans_router, responses=ERROR_RESPONSES)
api_router.include_router(sessions_router, responses=ERROR_RESPONSES)
api_router.include_router(practice_router, responses=ERROR_RESPONSES)
api_router.include_router(analytics_router, responses=ERROR_RESPONSES)
