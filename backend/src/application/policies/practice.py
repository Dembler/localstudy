from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass
from http import HTTPStatus
from typing import Protocol

from src.domain.entities import AnswerEvaluation, Assignment, Attempt
from src.domain.exceptions import NotFoundError


class AnswerChecker(Protocol):
    def is_correct(self, answer: str, expected: str) -> bool: ...


class ScoringPolicy(Protocol):
    @property
    def hint_penalty(self) -> int: ...

    def evaluate(self, is_correct: bool) -> AnswerEvaluation: ...


class AssignmentSelector(Protocol):
    def select(self, assignments: Sequence[Assignment], attempts: Sequence[Attempt]) -> Assignment:
        """Choose a supplied assignment; raise NotFoundError when none are available."""
        ...


class NormalizedAnswerChecker:
    def is_correct(self, answer: str, expected: str) -> bool:
        return " ".join(answer.casefold().split()) == " ".join(expected.casefold().split())


class HttpStatusAnswerChecker:
    def is_correct(self, answer: str, expected: str) -> bool:
        normalized = " ".join(expected.casefold().split())
        if not normalized.isdecimal():
            return False
        try:
            phrase = HTTPStatus(int(normalized)).phrase.casefold()
        except ValueError:
            return False
        return " ".join(answer.casefold().split()) == f"{normalized} {phrase}"


@dataclass(frozen=True)
class AnyAnswerChecker:
    checkers: tuple[AnswerChecker, ...]

    def is_correct(self, answer: str, expected: str) -> bool:
        return any(checker.is_correct(answer, expected) for checker in self.checkers)


@dataclass(frozen=True)
class FixedScoringPolicy:
    correct_score: int = 100
    incorrect_score: int = 35
    hint_penalty: int = 15

    def __post_init__(self) -> None:
        if any(
            value < 0 or value > 100
            for value in (self.correct_score, self.incorrect_score, self.hint_penalty)
        ):
            raise ValueError("scores and hint penalty must be between 0 and 100")

    def evaluate(self, is_correct: bool) -> AnswerEvaluation:
        score = self.correct_score if is_correct else self.incorrect_score
        return AnswerEvaluation(is_correct, score, max(0, score - self.hint_penalty))


class LeastMasteredAssignmentSelector:
    def select(self, assignments: Sequence[Assignment], attempts: Sequence[Attempt]) -> Assignment:
        if not assignments:
            raise NotFoundError("Нет доступных практических заданий")
        grouped: dict[str, list[Attempt]] = defaultdict(list)
        for attempt in attempts:
            grouped[attempt.assignment_id].append(attempt)
        return min(
            assignments,
            key=lambda item: (
                max((attempt.score for attempt in grouped[item.id]), default=-1),
                len(grouped[item.id]),
                item.difficulty,
            ),
        )
