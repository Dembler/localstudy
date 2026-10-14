import type { PracticeAssignment, PracticeAttempt } from '@/shared/api/types'
import type { UiAssignment, UiAttempt } from '@/shared/types/learning'

export function normalizeAssignment(item: PracticeAssignment): UiAssignment {
  return {
    id: item.id,
    lessonId: item.lesson_id,
    title: item.topic,
    topic: item.topic,
    prompt: item.prompt,
    difficulty: item.difficulty >= 4 ? 'Продвинутая' : item.difficulty >= 2 ? 'Средняя' : 'Базовая',
    estimatedMinutes: 15,
    answerPlaceholder: 'Введите короткий ответ',
  }
}

export function normalizeAttempt(item: PracticeAttempt): UiAttempt {
  return {
    id: item.id,
    submittedAt: item.created_at,
    isCorrect: item.is_correct,
    score: item.score,
    answer: item.answer,
    feedback: item.is_correct
      ? 'Решение принято.'
      : 'Попробуйте ещё раз и проверьте граничные случаи.',
  }
}
