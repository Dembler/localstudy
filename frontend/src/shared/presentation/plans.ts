import type { StudyPlan } from '@/shared/api/types'
import type { UiPlan } from '@/shared/types/learning'

export function planNameFromCourse(title: string): string {
  const normalized = title.trim().length >= 2 ? title.trim() : 'Учебный курс'
  const characters = Array.from(normalized)
  return characters.length <= 80 ? normalized : `${characters.slice(0, 79).join('').trimEnd()}…`
}

export function normalizePlan(
  plan: StudyPlan,
  previous?: UiPlan | null,
  targetCourseId?: string,
): UiPlan {
  return {
    id: plan.id,
    title: plan.name,
    courseId: targetCourseId ?? previous?.courseId ?? plan.course_ids.at(-1),
    startDate: plan.start_date,
    hasActivity: previous?.hasActivity ?? false,
    weeklyMinutes: plan.weekly_minutes,
    progress: previous?.progress ?? 0,
    forecastDate: previous?.forecastDate ?? 'уточняется',
    milestones: previous?.milestones ?? [],
  }
}
