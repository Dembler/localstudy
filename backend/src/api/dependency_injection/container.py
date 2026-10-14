import logging
from collections.abc import AsyncIterator

from dishka import AsyncContainer, Provider, Scope, alias, make_async_container, provide
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker

from src.api.settings import Settings
from src.application.policies.practice import (
    AnswerChecker,
    AnyAnswerChecker,
    AssignmentSelector,
    FixedScoringPolicy,
    HttpStatusAnswerChecker,
    LeastMasteredAssignmentSelector,
    NormalizedAnswerChecker,
    ScoringPolicy,
)
from src.application.policies.recommendations import (
    KeepMomentumRule,
    RecommendationPolicy,
    RuleBasedRecommendations,
    UpcomingSessionRule,
    WeakTopicsRule,
)
from src.application.policies.scheduling import SchedulePolicy, WeeklySchedulePolicy
from src.application.ports import (
    CatalogReader,
    Clock,
    PlanReader,
    PlanRepository,
    PracticeReader,
    PracticeRepository,
    SessionReader,
    SessionRepository,
)
from src.application.services import (
    AnalyticsService,
    CatalogService,
    PlanService,
    PracticeService,
    SessionService,
)
from src.application.services.prerequisites import PrerequisiteResolver
from src.infrastructure.clock import SystemClock
from src.infrastructure.database import make_engine, make_session_factory
from src.infrastructure.repositories import (
    SqlAlchemyCatalogRepository,
    SqlAlchemyPlanRepository,
    SqlAlchemyPracticeRepository,
    SqlAlchemySessionRepository,
)


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
    def catalog(self, session: AsyncSession) -> CatalogReader:
        return SqlAlchemyCatalogRepository(session)

    @provide(scope=Scope.REQUEST)
    def plans(self, session: AsyncSession) -> PlanRepository:
        return SqlAlchemyPlanRepository(session)

    @provide(scope=Scope.REQUEST)
    def sessions(self, session: AsyncSession) -> SessionRepository:
        return SqlAlchemySessionRepository(session)

    @provide(scope=Scope.REQUEST)
    def practice(self, session: AsyncSession) -> PracticeRepository:
        return SqlAlchemyPracticeRepository(session)

    plan_reader = alias(source=PlanRepository, provides=PlanReader)
    session_reader = alias(source=SessionRepository, provides=SessionReader)
    practice_reader = alias(source=PracticeRepository, provides=PracticeReader)

    @provide(scope=Scope.APP)
    def clock(self) -> Clock:
        return SystemClock()

    @provide(scope=Scope.APP)
    def scheduler(self) -> SchedulePolicy:
        return WeeklySchedulePolicy()

    @provide(scope=Scope.APP)
    def answer_checker(self) -> AnswerChecker:
        return AnyAnswerChecker((NormalizedAnswerChecker(), HttpStatusAnswerChecker()))

    @provide(scope=Scope.APP)
    def scoring(self) -> ScoringPolicy:
        return FixedScoringPolicy()

    @provide(scope=Scope.APP)
    def assignment_selector(self) -> AssignmentSelector:
        return LeastMasteredAssignmentSelector()

    @provide(scope=Scope.APP)
    def recommendations(self) -> RecommendationPolicy:
        return RuleBasedRecommendations((WeakTopicsRule(), UpcomingSessionRule()), KeepMomentumRule())

    prerequisites = provide(PrerequisiteResolver, scope=Scope.REQUEST)
    catalog_service = provide(CatalogService, scope=Scope.REQUEST)
    plan_service = provide(PlanService, scope=Scope.REQUEST)
    session_service = provide(SessionService, scope=Scope.REQUEST)
    practice_service = provide(PracticeService, scope=Scope.REQUEST)
    analytics_service = provide(AnalyticsService, scope=Scope.REQUEST)


def build_container(settings: Settings, logger: logging.Logger) -> AsyncContainer:
    return make_async_container(ApplicationProvider(settings, logger))
