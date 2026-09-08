import logging

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

logger = logging.getLogger("devx")


class AppException(Exception):
    """Base application exception. Every custom exception carries an
    HTTP status code, a human message and a machine-readable error_code."""

    status_code: int = status.HTTP_400_BAD_REQUEST
    error_code: str = "APP_ERROR"

    def __init__(self, message: str, error_code: str | None = None, status_code: int | None = None):
        self.message = message
        if error_code:
            self.error_code = error_code
        if status_code:
            self.status_code = status_code
        super().__init__(message)


class UserAlreadyExistsException(AppException):
    status_code = status.HTTP_409_CONFLICT
    error_code = "USER_ALREADY_EXISTS"


class InvalidCredentialsException(AppException):
    status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "INVALID_CREDENTIALS"


class UserNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "USER_NOT_FOUND"


class InactiveUserException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "INACTIVE_USER"


class SessionNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "SESSION_NOT_FOUND"


class SessionAlreadyCompletedException(AppException):
    status_code = status.HTTP_400_BAD_REQUEST
    error_code = "SESSION_ALREADY_COMPLETED"


class UnauthorizedSessionAccessException(AppException):
    status_code = status.HTTP_403_FORBIDDEN
    error_code = "UNAUTHORIZED_SESSION_ACCESS"


class InvalidMetricException(AppException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "INVALID_METRIC"


class InteractionNotFoundException(AppException):
    status_code = status.HTTP_404_NOT_FOUND
    error_code = "INTERACTION_NOT_FOUND"


class AIAnalysisException(AppException):
    status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "AI_ANALYSIS_ERROR"


def _error_body(message: str, error_code: str) -> dict:
    return {"success": False, "message": message, "error_code": error_code}


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppException)
    async def app_exception_handler(request: Request, exc: AppException):
        logger.warning("AppException %s on %s: %s", exc.error_code, request.url.path, exc.message)
        return JSONResponse(status_code=exc.status_code, content=_error_body(exc.message, exc.error_code))

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        logger.info("Validation error on %s: %s", request.url.path, exc.errors())
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content=_error_body("Validation failed: " + str(exc.errors()), "VALIDATION_ERROR"),
        )

    @app.exception_handler(Exception)
    async def unhandled_exception_handler(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s", request.url.path)
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content=_error_body("Internal server error", "INTERNAL_ERROR"),
        )
