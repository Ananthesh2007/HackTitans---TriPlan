import logging

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("triplan")


class AppError(Exception):
    """Raise this anywhere in the backend to send the standard error format."""

    def __init__(self, status_code: int, code: str, message: str, details=None):
        super().__init__(message)
        self.status_code = status_code
        self.code = code
        self.message = message
        self.details = details


def error_response(status_code: int, code: str, message: str, details=None) -> JSONResponse:
    body = {"code": code, "message": message}
    if details:
        body["details"] = details
    return JSONResponse(status_code=status_code, content={"error": body})


def _describe(error: dict) -> dict:
    """Turns one Pydantic error into {field, message}."""
    names = [
        part
        for part in error["loc"]
        if isinstance(part, str) and part not in ("body", "query", "path")
    ]
    field = names[-1] if names else "request"
    message = error["msg"].removeprefix("Value error, ")
    return {"field": field, "message": message}


def _label(field: str) -> str:
    return field.replace("_", " ").capitalize()


HTTP_CODES = {404: "not_found", 405: "method_not_allowed"}


def register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(AppError)
    async def handle_app_error(request: Request, exc: AppError):
        return error_response(exc.status_code, exc.code, exc.message, exc.details)

    @app.exception_handler(RequestValidationError)
    async def handle_validation_error(request: Request, exc: RequestValidationError):
        details = [_describe(error) for error in exc.errors()]
        first = details[0]
        message = f"{_label(first['field'])}: {first['message']}"
        extra = len(details) - 1
        if extra:
            message += f" (and {extra} more)"
        return error_response(422, "invalid_input", message, details)

    @app.exception_handler(StarletteHTTPException)
    async def handle_http_error(request: Request, exc: StarletteHTTPException):
        code = HTTP_CODES.get(exc.status_code, "http_error")
        message = exc.detail if isinstance(exc.detail, str) else "Request failed."
        return error_response(exc.status_code, code, message)

    @app.exception_handler(Exception)
    async def handle_unexpected_error(request: Request, exc: Exception):
        logger.exception("Unhandled error on %s %s", request.method, request.url.path)
        return error_response(
            500, "internal_error", "Something went wrong on the server. Try again in a moment."
        )