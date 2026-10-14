from typing import Annotated

from dishka.integrations.fastapi import DishkaRoute, FromDishka
from fastapi import APIRouter, Path, Query

from src.api.schemas import ApiResponse
from src.application.schemas import CourseDetail, CourseList, LessonPreview
from src.application.services import CatalogService
from src.domain.entities import CourseLevel

router = APIRouter(route_class=DishkaRoute, tags=["catalog"])


@router.get("/courses", response_model=ApiResponse[CourseList])
async def list_courses(
    service: FromDishka[CatalogService],
    level: Annotated[CourseLevel | None, Query()] = None,
    skill: Annotated[str | None, Query(min_length=2, max_length=60)] = None,
) -> ApiResponse[CourseList]:
    return ApiResponse(data=await service.list_courses(level, skill))


@router.get("/courses/search", response_model=ApiResponse[CourseList])
async def search_courses(
    service: FromDishka[CatalogService],
    q: Annotated[str, Query(min_length=2, max_length=100)],
) -> ApiResponse[CourseList]:
    return ApiResponse(data=await service.search_courses(q))


@router.get("/courses/{course_id}", response_model=ApiResponse[CourseDetail])
async def get_course(
    service: FromDishka[CatalogService],
    course_id: Annotated[str, Path(min_length=2, max_length=80)],
) -> ApiResponse[CourseDetail]:
    return ApiResponse(data=await service.get_course(course_id))


@router.get("/courses/{course_id}/prerequisites", response_model=ApiResponse[CourseList])
async def get_prerequisites(
    service: FromDishka[CatalogService],
    course_id: Annotated[str, Path(min_length=2, max_length=80)],
) -> ApiResponse[CourseList]:
    return ApiResponse(data=await service.prerequisites(course_id))


@router.get("/lessons/{lesson_id}/preview", response_model=ApiResponse[LessonPreview])
async def preview_lesson(
    service: FromDishka[CatalogService],
    lesson_id: Annotated[str, Path(min_length=2, max_length=80)],
) -> ApiResponse[LessonPreview]:
    return ApiResponse(data=await service.lesson_preview(lesson_id))
