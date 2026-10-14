import logging
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.domain.exceptions import AppError


def _request_id(request: Request) -> str:
    return getattr(request.state, "request_id", str(uuid4()))


def _error(request: Request, status_code: int, code: str, message: str, details: object) -> JSONResponse:
    return JSONResponse(
        status_code=status_code,
        content={
            "status": "error",
            "error": {
                "code": code,
                "message": message,
                "details": details,
                "request_id": _request_id(request),
            },
        },
    )


def register_exception_handlers(app: FastAPI, logger: logging.Logger) -> None:
    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
        return _error(request, exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
        details = [
            {"location": list(error["loc"]), "message": error["msg"], "type": error["type"]}
            for error in exc.errors()
        ]
        return _error(request, 422, "request_validation", "Ошибка проверки запроса", details)

    @app.exception_handler(StarletteHTTPException)
    async def http_error_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
        code = {
            404: "not_found",
            405: "method_not_allowed",
        }.get(exc.status_code, "http_error")
        message = {
            404: "Ресурс не найден",
            405: "Метод не поддерживается",
        }.get(exc.status_code, "Ошибка HTTP-запроса")
        details: object = {} if isinstance(exc.detail, str) else exc.detail
        return _error(request, exc.status_code, code, message, details)

    @app.exception_handler(Exception)
    async def unexpected_error_handler(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("unhandled application error", extra={"request_id": _request_id(request)})
        return _error(request, 500, "internal_error", "Произошла непредвиденная ошибка", {})
