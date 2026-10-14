import type { CourseSummary } from '@/shared/api/types'
import type { UiCourse } from '@/shared/types/learning'

const levelLabels: Record<CourseSummary['level'], string> = {
  beginner: 'Начальный',
  intermediate: 'Средний',
  advanced: 'Продвинутый',
}

export function normalizeCourse(course: CourseSummary): UiCourse {
  return {
    id: course.id,
    title: course.title,
    description: course.description,
    category: course.skills.includes('SQL') ? 'Данные' : 'Разработка',
    level: levelLabels[course.level] ?? course.level,
    durationHours: Math.max(1, Math.round(course.duration_minutes / 60)),
    lessonsCount: course.lesson_count,
    skills: course.skills,
  }
}
