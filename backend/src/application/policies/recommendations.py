from dataclasses import dataclass
from typing import Protocol

from src.application.schemas import Recommendation, WeakTopic
from src.domain.entities import Lesson, StudySession


@dataclass(frozen=True)
class RecommendationContext:
    weak_topics: list[WeakTopic]
    planned_sessions: list[StudySession]
    lessons: dict[str, Lesson]
    fallback_assignment_id: str | None = None


class RecommendationPolicy(Protocol):
    def recommend(self, context: RecommendationContext) -> list[Recommendation]: ...


class RecommendationRule(Protocol):
    def recommend(self, context: RecommendationContext) -> list[Recommendation]: ...


class WeakTopicsRule:
    def recommend(self, context: RecommendationContext) -> list[Recommendation]:
        return [
            Recommendation(
                kind="practice",
                title=f"Закрепить тему «{topic.topic}»",
                reason=f"Текущий средний результат — {topic.average_score}%",
            )
            for topic in context.weak_topics[:2]
        ]


class UpcomingSessionRule:
    def recommend(self, context: RecommendationContext) -> list[Recommendation]:
        if not context.planned_sessions:
            return []
        upcoming = min(context.planned_sessions, key=lambda item: item.scheduled_for)
        lesson = context.lessons.get(upcoming.lesson_id)
        return [
            Recommendation(
                kind="schedule",
                title=f"Подготовиться к занятию «{lesson.title if lesson else 'Следующий урок'}»",
                reason="Это ближайшее запланированное занятие",
                action_id=upcoming.id,
            )
        ]


class KeepMomentumRule:
    def recommend(self, context: RecommendationContext) -> list[Recommendation]:
        if context.fallback_assignment_id is None:
            return []
        return [
            Recommendation(
                kind="practice",
                title="Сохранить темп обучения",
                reason="Доступно короткое практическое задание",
                action_id=context.fallback_assignment_id,
            )
        ]


@dataclass(frozen=True)
class RuleBasedRecommendations:
    rules: tuple[RecommendationRule, ...]
    fallback: RecommendationRule

    def recommend(self, context: RecommendationContext) -> list[Recommendation]:
        items = [item for rule in self.rules for item in rule.recommend(context)]
        return items or self.fallback.recommend(context)
