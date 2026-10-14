from typing import Any


class AppError(Exception):
    code = "application_error"

    def __init__(self, message: str, *, details: dict[str, Any] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(AppError):
    code = "not_found"


class ConflictError(AppError):
    code = "conflict"


class InvalidStateError(AppError):
    code = "invalid_state"


class ValidationError(AppError):
    code = "business_validation"
