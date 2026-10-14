import type { StudySession } from '@/shared/api/types'
import type { UiSession } from '@/shared/types/learning'

export function normalizeSession(session: StudySession, courseTitle: string): UiSession {
  return {
    id: session.id,
    planId: session.plan_id,
    title: session.lesson_title,
    courseTitle,
    startsAt: session.scheduled_for,
    durationMinutes: session.duration_minutes,
    status:
      session.status === 'planned'
        ? 'scheduled'
        : session.status === 'in_progress'
          ? 'in_progress'
          : session.status,
  }
}
