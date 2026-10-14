from src.application.policies.practice import AnswerChecker, AssignmentSelector, ScoringPolicy
from src.application.ports import CatalogReader, PlanReader, PracticeRepository
from src.application.schemas import (
    AssignmentView,
    AttemptHistory,
    AttemptView,
    HintView,
    RetryView,
)
from src.application.services.lookups import require_assignment, require_plan
from src.domain.entities import (
    Assignment,
    Attempt,
)
from src.domain.exceptions import ConflictError, NotFoundError, ValidationError


class PracticeService:
    def __init__(
        self,
        practice: PracticeRepository,
        plans: PlanReader,
        catalog: CatalogReader,
        checker: AnswerChecker,
        scoring: ScoringPolicy,
        selector: AssignmentSelector,
    ) -> None:
        self._practice = practice
        self._plans = plans
        self._catalog = catalog
        self._checker = checker
        self._scoring = scoring
        self._selector = selector

    async def next_assignment(
        self, *, plan_id: str | None = None, course_id: str | None = None
    ) -> AssignmentView:
        if course_id is not None and plan_id is None:
            raise ValidationError("Курс можно уточнить только вместе с учебным планом")
        assignments = await self._practice.list_assignments()
        if plan_id is not None:
            plan = await require_plan(self._plans, plan_id)
            if course_id is not None and course_id not in plan.course_ids:
                raise ConflictError(
                    "Курс не относится к этому учебному плану",
                    details={"plan_id": plan_id, "course_id": course_id},
                )
            course_ids = [course_id] if course_id is not None else plan.course_ids
            lesson_ids = {item.id for item in await self._catalog.list_lessons(course_ids)}
            assignments = [item for item in assignments if item.lesson_id in lesson_ids]
        if not assignments:
            raise NotFoundError("Нет доступных практических заданий")
        attempts = await self._practice.list_attempts()
        assignment = self._selector.select(assignments, attempts)
        count = sum(item.assignment_id == assignment.id for item in attempts)
        return self._assignment_view(assignment, count)

    async def submit_attempt(self, assignment_id: str, answer: str) -> AttemptView:
        await require_assignment(self._practice, assignment_id)
        expected = await self._practice.answer_for(assignment_id)
        if expected is None:
            raise NotFoundError("Задание не найдено")
        evaluation = self._scoring.evaluate(self._checker.is_correct(answer, expected))
        attempt = await self._practice.record_attempt(
            assignment_id=assignment_id,
            answer=answer,
            evaluation=evaluation,
        )
        return self._attempt_view(attempt)

    async def hint(self, assignment_id: str) -> HintView:
        assignment = await require_assignment(self._practice, assignment_id)
        await self._practice.mark_hint_requested(assignment_id)
        return HintView(
            assignment_id=assignment.id, hint=assignment.hint, penalty_percent=self._scoring.hint_penalty
        )

    async def retry(self, assignment_id: str) -> RetryView:
        assignment = await require_assignment(self._practice, assignment_id)
        attempts = await self._practice.list_attempts(assignment_id)
        if not attempts:
            raise ConflictError("Перед повторной попыткой отправьте первый ответ")
        await self._practice.clear_hint_marker(assignment_id)
        return RetryView(
            assignment=self._assignment_view(assignment, len(attempts)),
            previous_best_score=max(item.score for item in attempts),
            message="Повторная попытка готова: подсказка сброшена",
        )

    async def attempt_history(self, assignment_id: str) -> AttemptHistory:
        await require_assignment(self._practice, assignment_id)
        attempts = await self._practice.list_attempts(assignment_id)
        return AttemptHistory(
            items=[self._attempt_view(item) for item in attempts],
            total=len(attempts),
            best_score=max((item.score for item in attempts), default=0),
        )

    @staticmethod
    def _assignment_view(assignment: Assignment, attempts_count: int) -> AssignmentView:
        return AssignmentView(
            id=assignment.id,
            lesson_id=assignment.lesson_id,
            topic=assignment.topic,
            prompt=assignment.prompt,
            difficulty=assignment.difficulty,
            attempts_count=attempts_count,
        )

    @staticmethod
    def _attempt_view(attempt: Attempt) -> AttemptView:
        return AttemptView(
            id=attempt.id,
            assignment_id=attempt.assignment_id,
            answer=attempt.answer,
            is_correct=attempt.is_correct,
            score=attempt.score,
            hint_used=attempt.hint_used,
            created_at=attempt.created_at,
        )
