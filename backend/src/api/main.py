from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from dishka.integrations.fastapi import setup_dishka
from fastapi import FastAPI
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker
from starlette.middleware.cors import CORSMiddleware

from src.api.dependency_injection import build_container
from src.api.exception_handlers import register_exception_handlers
from src.api.middleware import RequestLoggingMiddleware
from src.api.routers import api_router
from src.api.settings import Settings, get_settings
from src.infrastructure.database import Base
from src.infrastructure.logging import configure_logging
from src.infrastructure.seed import seed_demo_data


def create_app(settings: Settings | None = None) -> FastAPI:
    resolved = settings or get_settings()
    logger = configure_logging(resolved.log_level, resolved.log_file)
    container = build_container(resolved, logger)

    @asynccontextmanager
    async def lifespan(app: FastAPI) -> AsyncIterator[None]:
        engine: AsyncEngine | None = None
        try:
            engine = await container.get(AsyncEngine)
            session_factory = await container.get(async_sessionmaker[AsyncSession])
            async with engine.begin() as connection:
                await connection.run_sync(Base.metadata.create_all)
            await seed_demo_data(session_factory)
            logger.info("application started", extra={"environment": resolved.app_env})
            yield
        finally:
            logger.info("application stopping")
            if engine is not None:
                await engine.dispose()
            await container.close()

    app = FastAPI(
        title=resolved.app_name,
        version="0.1.0",
        description="Adaptive learning tracker with 25 focused business operations.",
        lifespan=lifespan,
    )
    setup_dishka(container, app)
    app.state.dishka_container = container
    app.add_middleware(
        CORSMiddleware,
        allow_origins=resolved.cors_origins,
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.add_middleware(RequestLoggingMiddleware, logger=logger)

    @app.get("/health", tags=["technical"], include_in_schema=False)
    async def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(api_router, prefix=resolved.api_prefix)
    register_exception_handlers(app, logger)
    return app


app = create_app()


__all__ = ["app", "create_app"]
