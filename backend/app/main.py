from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.routes.auth_strava import router as auth_strava_router
from app.api.routes.health import router as health_router
from app.api.routes.sync import router as sync_router
from app.core.config import get_settings
from app.db.session import init_db


@asynccontextmanager
async def lifespan(_: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        lifespan=lifespan,
    )
    app.include_router(auth_strava_router)
    app.include_router(health_router)
    app.include_router(sync_router)
    return app


app = create_app()
