export interface UiCourse {
  id: string
  title: string
  description: string
  level: string
  durationHours: number
  lessonsCount: number
  skills: string[]
  category: string
  progress?: number
}

export interface UiMilestone {
  id: string
  title: string
  courseTitle: string
  dueLabel: string
  status: 'done' | 'current' | 'next'
  durationMinutes: number
}

export interface UiPlan {
  id: string
  title: string
  courseId?: string
  startDate?: string
  hasActivity?: boolean
  weeklyMinutes: number
  progress: number
  forecastDate: string
  milestones: UiMilestone[]
}

export interface UiSession {
  id: string
  planId: string
  title: string
  courseTitle: string
  startsAt: string
  durationMinutes: number
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
}

export interface UiAssignment {
  id: string
  lessonId: string
  title: string
  topic: string
  prompt: string
  difficulty: string
  estimatedMinutes: number
  answerPlaceholder: string
  hint?: string
}

export interface UiAttempt {
  id: string
  submittedAt: string
  isCorrect: boolean
  score: number
  answer: string
  feedback: string
}

export interface UiSkill {
  id: string
  name: string
  value: number
  trend: number
}

export interface UiRecommendation {
  id: string
  title: string
  reason: string
  topic: string
  estimatedMinutes: number
  to: '/practice' | '/sessions'
}

export interface AnalyticsOverviewView {
  progress: number
  studiedMinutes: number
  completedSessions: number
  streakDays: number
}
export interface WeakTopicView {
  id: string
  title: string
  reason: string
  score: number
}
