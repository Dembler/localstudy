from datetime import date, timedelta
from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, Query, status

from src.api.schemas import (
    ApiResponse,
    CompleteSessionRequest,
    CreateSessionRequest,
    RescheduleSessionRequest,
)
from src.application.schemas import SessionCalendar, SessionView
from src.application.services import SessionService

router = APIRouter(route_class=DishkaRoute, prefix="/sessions", tags=["study sessions"])
SessionId = Annotated[str, Path(min_length=2, max_length=80)]


@router.get("/calendar", response_model=ApiResponse[SessionCalendar])
async def get_calendar(
    service: FromDishka[SessionService],
    from_date: Annotated[date | None, Query()] = None,
    to_date: Annotated[date | None, Query()] = None,
) -> ApiResponse[SessionCalendar]:
    start = from_date or date.today()
    end = to_date or start + timedelta(days=30)
    return ApiResponse(data=await service.calendar(start, end))


@router.post("", response_model=ApiResponse[SessionView], status_code=status.HTTP_201_CREATED)
async def create_session(
    payload: CreateSessionRequest, service: FromDishka[SessionService]
) -> ApiResponse[SessionView]:
    return ApiResponse(data=await service.create_session(**payload.model_dump()))


@router.post("/{session_id}/start", response_model=ApiResponse[SessionView])
async def start_session(
    session_id: SessionId, service: FromDishka[SessionService]
) -> ApiResponse[SessionView]:
    return ApiResponse(data=await service.start_session(session_id))


@router.post("/{session_id}/complete", response_model=ApiResponse[SessionView])
async def complete_session(
    session_id: SessionId,
    payload: CompleteSessionRequest,
    service: FromDishka[SessionService],
) -> ApiResponse[SessionView]:
    return ApiResponse(data=await service.complete_session(session_id, payload.score))


@router.post("/{session_id}/reschedule", response_model=ApiResponse[SessionView])
async def reschedule_session(
    session_id: SessionId,
    payload: RescheduleSessionRequest,
    service: FromDishka[SessionService],
) -> ApiResponse[SessionView]:
    return ApiResponse(data=await service.reschedule_session(session_id, payload.scheduled_for))


@router.delete("/{session_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_session(session_id: SessionId, service: FromDishka[SessionService]) -> None:
    await service.delete_session(session_id)
