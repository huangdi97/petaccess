"""Unified API error format (design #31: 统一 error)."""

from fastapi import Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import IntegrityError


class ApiError(Exception):
    """Domain error carrying a stable machine code."""

    status_code = 400
    code = "bad_request"

    def __init__(
        self,
        message: str,
        *,
        code: str | None = None,
        status_code: int | None = None,
        details: dict | None = None,
    ):
        self.message = message
        if code:
            self.code = code
        if status_code:
            self.status_code = status_code
        self.details = details or {}
        super().__init__(message)


class NotFound(ApiError):
    status_code = 404
    code = "not_found"


class PermissionDenied(ApiError):
    status_code = 403
    code = "permission_denied"


class Unauthorized(ApiError):
    status_code = 401
    code = "unauthorized"


class Conflict(ApiError):
    status_code = 409
    code = "conflict"


class RateLimited(ApiError):
    status_code = 429
    code = "rate_limited"


def _payload(
    request: Request, code: str, message: str, status_code: int, details: dict | None = None
) -> JSONResponse:
    request_id = getattr(request.state, "request_id", None) or ""
    return JSONResponse(
        status_code=status_code,
        content={
            "error": {
                "code": code,
                "message": message,
                "request_id": request_id,
                "details": details or {},
            }
        },
    )


def install_error_handlers(app) -> None:
    @app.exception_handler(ApiError)
    async def api_error_handler(request: Request, exc: ApiError):
        return _payload(request, exc.code, exc.message, exc.status_code, exc.details)

    @app.exception_handler(RequestValidationError)
    async def validation_handler(request: Request, exc: RequestValidationError):
        return _payload(
            request, "validation_error", "请求参数校验失败", 422, {"errors": exc.errors()[:20]}
        )

    @app.exception_handler(IntegrityError)
    async def integrity_handler(request: Request, exc: IntegrityError):
        return _payload(request, "integrity_error", "数据完整性冲突", 409)

    @app.exception_handler(Exception)
    async def unhandled_handler(request: Request, exc: Exception):
        return _payload(request, "internal_error", "服务器内部错误", 500)
