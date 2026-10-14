import logging
from dataclasses import replace
from datetime import date, datetime, time, timedelta

import pytest

from src.application.policies.practice import (
    AnyAnswerChecker,
    FixedScoringPolicy,
    HttpStatusAnswerChecker,
    LeastMasteredAssignmentSelector,
    NormalizedAnswerChecker,
)
from src.application.policies.recommendations import (
    KeepMomentumRule,
    RecommendationContext,
    RuleBasedRecommendations,
    WeakTopicsRule,
)
from src.application.policies.scheduling import WeeklySchedulePolicy
from src.application.schemas import Recommendation, WeakTopic
from src.application.services import PlanService, PracticeService
from src.application.services.prerequisites import PrerequisiteResolver
from src.domain.entities import Assignment, SessionStatus, StudyPlan, StudySession
from src.domain.exceptions import NotFoundError
from tests.memory_repositories import MemoryCatalog, MemoryPlans, MemoryPractice, MemorySessions


@pytest.mark.parametrize(
    ("answer", "expected", "correct"),
    [
        (" BOOL  ", "bool", True),
        ("201 Created", "201", True),
        ("201 404", "201", False),
        ("unknown", "bool", False),
        ("999 Unknown", "999", False),
        ("  hello   WORLD ", "hello world", True),
    ],
)
def test_default_answer_rules(answer: str, expected: str, correct: bool) -> None:
    checker = AnyAnswerChecker((NormalizedAnswerChecker(), HttpStatusAnswerChecker()))
    assert checker.is_correct(answer, expected) is correct


def test_schedule_is_replaceable_and_does_not_mutate_completed_sessions() -> None:
    today = date(2026, 10, 14)
    plan = StudyPlan("p", "Plan", 180, today + timedelta(days=2), [], datetime(2026, 10, 14))
    sessions = [
        StudySession(
            str(index),
            "p",
            "lesson",
            datetime(2026, 10, 14 + index),
            45,
            SessionStatus.COMPLETED if index == 0 else SessionStatus.PLANNED,
        )
        for index in range(5)
    ]
    policy = WeeklySchedulePolicy(day_offsets=(1, 4), starts_at=time(10), maximum_minutes=80)
    updated = policy.distribute(plan, list(reversed(sessions)), today)
    assert [item.id for item in updated] == ["1", "2", "3", "4"]
    assert [item.scheduled_for.date() for item in updated] == [
        plan.start_date + timedelta(days=day) for day in (1, 4, 8, 11)
    ]
    assert all(item.scheduled_for.hour == 10 and item.duration_minutes == 80 for item in updated)
    assert sessions[0].status == SessionStatus.COMPLETED
    assert all(item.duration_minutes == 45 for item in sessions)


async def test_practice_service_accepts_custom_answer_and_scoring_policies() -> None:
    class CustomChecker:
        def is_correct(self, answer: str, expected: str) -> bool:
            return answer == "alternative"

    repository = MemoryPractice([Assignment("q", "lesson", "Topic", "Prompt", "Hint", 1)], {"q": "canonical"})
    service = PracticeService(
        repository,
        MemoryPlans([]),
        MemoryCatalog([], []),
        CustomChecker(),
        FixedScoringPolicy(90, 20, 30),
        LeastMasteredAssignmentSelector(),
    )
    hint = await service.hint("q")
    result = await service.submit_attempt("q", "alternative")
    assert hint.penalty_percent == 30
    assert result.is_correct and result.score == 60 and result.hint_used
    assert FixedScoringPolicy(90, 20, 30).evaluate(False).hinted_score == 0


def test_recommendations_accept_additional_rules_and_use_fallback_only_when_needed() -> None:
    class CustomRule:
        def recommend(self, context: RecommendationContext) -> list[Recommendation]:
            return [Recommendation(kind="custom", title="Custom", reason="Configured rule")]

    context = RecommendationContext([], [], {}, fallback_assignment_id="q")
    engine = RuleBasedRecommendations((CustomRule(),), KeepMomentumRule())
    assert [item.kind for item in engine.recommend(context)] == ["custom"]
    engine = RuleBasedRecommendations((WeakTopicsRule(),), KeepMomentumRule())
    assert engine.recommend(context)[0].action_id == "q"
    weak = WeakTopic(topic="Types", average_score=40, attempts=2, suggested_action="Repeat")
    result = engine.recommend(replace(context, weak_topics=[weak]))
    assert len(result) == 1 and result[0].action_id is None


def test_assignment_selector_prioritizes_unattempted_work_and_handles_empty_input() -> None:
    assignments = [
        Assignment("hard", "lesson", "T", "P", "H", 4),
        Assignment("easy", "lesson", "T", "P", "H", 1),
    ]
    selector = LeastMasteredAssignmentSelector()
    assert selector.select(assignments, []).id == "easy"
    with pytest.raises(NotFoundError):
        selector.select([], [])


async def test_plan_service_uses_injected_scheduler_and_clock() -> None:
    today = date(2026, 10, 14)
    moment = datetime(2026, 10, 14, 8)

    class FixedClock:
        def today(self) -> date:
            return today

        def now(self) -> datetime:
            return moment

    class CustomScheduler:
        def distribute(
            self, plan: StudyPlan, sessions: list[StudySession], today: date
        ) -> list[StudySession]:
            return [replace(sessions[0], duration_minutes=99, scheduled_for=datetime.combine(today, time(9)))]

    plans = MemoryPlans([StudyPlan("p", "Plan", 180, today, [], moment)])
    sessions = MemorySessions([StudySession("s", "p", "lesson", moment, 45, SessionStatus.PLANNED)])
    catalog = MemoryCatalog([], [])
    service = PlanService(
        plans,
        catalog,
        sessions,
        PrerequisiteResolver(catalog),
        CustomScheduler(),
        FixedClock(),
        logging.getLogger("test"),
    )
    result = await service.rebalance("p")
    assert result.sessions_updated == 1
    stored = await sessions.get_session("s")
    assert stored.duration_minutes == 99 and stored.scheduled_for == datetime(2026, 10, 14, 9)
