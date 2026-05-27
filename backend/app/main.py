from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from .api import router
from . import services
from .database import Database


class UTF8JSONResponse(JSONResponse):
    """强制 charset=utf-8，避免中文在响应里被转义/乱码。"""

    media_type = "application/json; charset=utf-8"


def _validation_message(exc: RequestValidationError) -> str:
    errors = exc.errors()
    if not errors:
        return "请求参数不正确"
    message = str(errors[0].get("msg") or "请求参数不正确")
    return message.removeprefix("Value error, ")


def create_app(database_url: str | None = None) -> FastAPI:
    app = FastAPI(
        title="出海船员管理系统 API",
        version="1.0.0",
        default_response_class=UTF8JSONResponse,
    )
    app.state.database = Database(database_url)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        return UTF8JSONResponse(
            status_code=400,
            content={"success": False, "message": _validation_message(exc)},
        )

    @app.exception_handler(services.ApiError)
    async def api_error_handler(request: Request, exc: services.ApiError):
        return UTF8JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "message": exc.message},
        )

    app.include_router(router)
    return app


app = create_app()
