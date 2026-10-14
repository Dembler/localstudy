import logging
from collections.abc import AsyncIterator

from dishka import AsyncContainer, Provider, Scope, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.settings import Settings
from src.application.ports import LearningRepository
from src.application.services import LearningService
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositories import SqlAlchemyLearningRepository


class ApplicationProvider(Provider):
    def __init__(self, settings: Settings, logger: logging.Logger) -> None:
        super().__init__()
        self._settings = settings
        self._logger = logger

    @provide(scope=Scope.APP)
    def settings(self) -> Settings:
        return self._settings

    @provide(scope=Scope.APP)
    def logger(self) -> logging.Logger:
        return self._logger

    @provide(scope=Scope.APP)
    def engine(self, settings: Settings) -> AsyncEngine:
        return make_engine(settings.database_url, echo=settings.app_env == "debug")

    @provide(scope=Scope.APP)
    def session_factory(self, engine: AsyncEngine) -> async_sessionmaker[AsyncSession]:
        return make_session_factory(engine)

    @provide(scope=Scope.REQUEST)
    async def session(self, session_factory: async_sessionmaker[AsyncSession]) -> AsyncIterator[AsyncSession]:
        async with session_factory() as session:
            yield session

    @provide(scope=Scope.REQUEST)
    def repository(self, session: AsyncSession) -> LearningRepository:
        return SqlAlchemyLearningRepository(session)

    @provide(scope=Scope.REQUEST)
    def learning_service(self, repository: LearningRepository, logger: logging.Logger) -> LearningService:
        return LearningService(repository, logger)


def build_container(settings: Settings, logger: logging.Logger) -> AsyncContainer:
    return make_async_container(ApplicationProvider(settings, logger))
