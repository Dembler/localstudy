import { createPinia, disposePinia, type Pinia } from 'pinia'
import { createApp } from 'vue'
import { afterEach, describe, expect, it, vi } from 'vitest'

import { ApiError } from '@/shared/api/client'
import type { PracticeAssignment, PracticeAttempt, StudySession } from '@/shared/api/types'
import { normalizeAssignment } from '@/shared/presentation/practice'
import {
  ANALYTICS_GATEWAY,
  CATALOG_GATEWAY,
  PLANS_GATEWAY,
  PLAN_STORAGE,
  PRACTICE_GATEWAY,
  SESSIONS_GATEWAY,
  type PlansGateway,
  type PracticeGateway,
} from '@/shared/services/ports'
import { BrowserPlanStorage, PLAN_STORAGE_KEY } from '@/shared/storage/plan-storage'
import type { UiPlan } from '@/shared/types/learning'
import { useAnalyticsStore } from './analytics'
import { useCatalogStore } from './catalog'
import { usePlanStore } from './plans'
import { usePracticeStore } from './practice'
import { useSessionsStore } from './sessions'

const piniaInstances: Pinia[] = []
afterEach(() => {
  piniaInstances.splice(0).forEach(disposePinia)
})

const savedPlan: UiPlan = {
  id: 'plan-a',
  title: 'Learning',
  courseId: 'course-a',
  startDate: '2026-10-14',
  weeklyMinutes: 180,
  progress: 0,
  forecastDate: '',
  milestones: [],
}
const assignment: PracticeAssignment = {
  id: 'assignment',
  lesson_id: 'lesson',
  topic: 'Types',
  prompt: 'Question',
  difficulty: 1,
  attempts_count: 0,
}
const session: StudySession = {
  id: 'session',
  plan_id: savedPlan.id,
  lesson_id: 'lesson',
  lesson_title: 'Types',
  scheduled_for: '2026-10-15T12:00:00',
  duration_minutes: 45,
  status: 'planned',
  started_at: null,
  completed_at: null,
  score: null,
}

function createTestApp() {
  const app = createApp({})
  const pinia = createPinia()
  piniaInstances.push(pinia)
  app.use(pinia)
  return app
}

function setup() {
  const app = createTestApp()
  const storage = {
    read: vi.fn(() => structuredClone(savedPlan)),
    write: vi.fn(() => true),
    clear: vi.fn(),
  }
  const plansApi = {
    createPlan: vi.fn<PlansGateway['createPlan']>().mockResolvedValue({
      id: 'new-plan',
      name: 'New',
      weekly_minutes: 180,
      course_ids: ['course-a'],
      start_date: '2026-10-14',
      created_at: '2026-10-14T12:00:00',
    }),
    getPlanForecast: vi.fn<PlansGateway['getPlanForecast']>().mockResolvedValue({
      plan_id: savedPlan.id,
      remaining_minutes: 100,
      weekly_minutes: 180,
      expected_completion: '2026-11-14',
      weeks_remaining: 1,
      confidence: 'low',
    }),
    updatePlanWorkload: vi.fn<PlansGateway['updatePlanWorkload']>(),
    rebalancePlan: vi.fn<PlansGateway['rebalancePlan']>(),
    addPlanGoal: vi.fn<PlansGateway['addPlanGoal']>(),
    deletePlan: vi.fn<PlansGateway['deletePlan']>(),
    deletePlanGoal: vi.fn<PlansGateway['deletePlanGoal']>(),
    removePlanCourse: vi.fn<PlansGateway['removePlanCourse']>(),
  }
  const practiceApi = {
    getNextAssignment: vi.fn<PracticeGateway['getNextAssignment']>().mockResolvedValue(assignment),
    listAttempts: vi
      .fn<PracticeGateway['listAttempts']>()
      .mockResolvedValue({ items: [], total: 0, best_score: 0 }),
    submitAttempt: vi.fn<PracticeGateway['submitAttempt']>(),
    requestHint: vi
      .fn<PracticeGateway['requestHint']>()
      .mockResolvedValue({ assignment_id: 'assignment', hint: 'Hint', penalty_percent: 15 }),
    retryAssignment: vi.fn<PracticeGateway['retryAssignment']>(),
  }
  const sessionsApi = {
    getSessionCalendar: vi.fn().mockResolvedValue({
      items: [session],
      total: 1,
      from_date: '2026-10-14',
      to_date: '2028-10-14',
    }),
    scheduleSession: vi.fn().mockResolvedValue(session),
    startSession: vi.fn().mockResolvedValue({ ...session, status: 'in_progress' }),
    completeSession: vi.fn().mockResolvedValue({ ...session, status: 'completed' }),
    rescheduleSession: vi.fn(),
    deleteSession: vi.fn(),
  }
  const analyticsApi = {
    getOverview: vi.fn().mockResolvedValue({
      courses_in_plan: 1,
      completed_sessions: 2,
      study_minutes: 90,
      average_score: 85,
      completion_percent: 50,
    }),
    getSkills: vi.fn().mockResolvedValue({
      items: [{ skill: 'Python', progress_percent: 50, level: 'developing' }],
    }),
    getStreak: vi
      .fn()
      .mockResolvedValue({ current_days: 2, longest_days: 3, last_study_date: '2026-10-14' }),
    getWeakTopics: vi.fn().mockResolvedValue({ items: [] }),
    getRecommendations: vi.fn().mockResolvedValue({ items: [] }),
  }
  app.provide(PLAN_STORAGE, storage)
  app.provide(PLANS_GATEWAY, plansApi)
  app.provide(PRACTICE_GATEWAY, practiceApi)
  app.provide(SESSIONS_GATEWAY, sessionsApi)
  app.provide(ANALYTICS_GATEWAY, analyticsApi)
  const stores = app.runWithContext(() => ({
    plans: usePlanStore(),
    practice: usePracticeStore(),
    sessions: useSessionsStore(),
    analytics: useAnalyticsStore(),
  }))
  return { ...stores, storage, plansApi, practiceApi, sessionsApi, analyticsApi }
}

describe('feature stores with substituted dependencies', () => {
  it('loads the catalog using only its own gateway', async () => {
    const app = createTestApp()
    const gateway = {
      listCourses: vi.fn().mockResolvedValue({ items: [], total: 0 }),
      searchCourses: vi.fn(),
      getCourse: vi.fn(),
    }
    app.provide(CATALOG_GATEWAY, gateway)
    const catalog = app.runWithContext(() => useCatalogStore())
    await catalog.loadCatalog()
    expect(gateway.listCourses).toHaveBeenCalledOnce()
    expect(catalog.demoMode).toBe(false)
  })

  it('keeps a saved plan when forecast refresh fails', async () => {
    const state = setup()
    state.plansApi.getPlanForecast.mockRejectedValue(new Error('offline'))
    await state.plans.loadPlan()
    expect(state.plans.plan?.id).toBe(savedPlan.id)
    expect(state.plans.error).toContain('Сохранённый план')
    expect(state.storage.clear).not.toHaveBeenCalled()
  })

  it('discards a saved plan that no longer exists', async () => {
    const state = setup()
    state.plansApi.getPlanForecast.mockRejectedValue(
      new ApiError('missing', { status: 404, code: 'not_found' }),
    )
    await state.plans.loadPlan()
    expect(state.plans.plan).toBeNull()
    expect(state.storage.clear).toHaveBeenCalledOnce()
  })

  it('keeps a newly created plan even if its forecast fails', async () => {
    const state = setup()
    state.plansApi.getPlanForecast.mockRejectedValue(new Error('offline'))
    const created = await state.plans.createNewPlan({
      weeklyMinutes: 180,
      course: {
        id: 'course-a',
        title: 'New',
        description: '',
        level: 'Начальный',
        durationHours: 1,
        lessonsCount: 1,
        skills: [],
        category: 'Разработка',
      },
    })
    expect(created).toBe(true)
    expect(state.plans.plan?.id).toBe('new-plan')
    expect(state.storage.write).toHaveBeenCalled()
  })

  it('filters sessions to the active plan and records completed activity', async () => {
    const state = setup()
    await state.plans.loadPlan()
    state.sessionsApi.getSessionCalendar.mockResolvedValue({
      items: [session, { ...session, id: 'other', plan_id: 'other' }],
      total: 2,
      from_date: '',
      to_date: '',
    })
    await state.sessions.loadSessions()
    expect(state.sessions.sessions.map((item) => item.id)).toEqual(['session'])
    await state.sessions.advanceSession('session')
    await state.sessions.advanceSession('session')
    expect(state.plans.plan?.hasActivity).toBe(true)
    expect(state.storage.write).toHaveBeenCalled()
  })

  it('resets sessions, practice and analytics when the plan is cleared', async () => {
    const state = setup()
    await state.plans.loadPlan()
    await Promise.all([
      state.sessions.loadSessions(),
      state.practice.loadPractice(),
      state.analytics.loadAnalytics(),
    ])
    await state.practice.requestPracticeHint()
    expect(state.practice.visibleHint).toBe('Hint')
    state.plans.clearActivePlan()
    expect(state.sessions.sessions).toEqual([])
    expect(state.practice.assignment).toBeNull()
    expect(state.practice.visibleHint).toBe('')
    expect(state.analytics.overview.progress).toBe(0)
    expect(state.analytics.skills).toEqual([])
  })

  it('ignores an attempt response from the previous plan', async () => {
    const state = setup()
    await state.plans.loadPlan()
    state.practice.assignment = normalizeAssignment(assignment)
    let finish!: (attempt: PracticeAttempt) => void
    state.practiceApi.submitAttempt.mockImplementation(
      () =>
        new Promise((resolve) => {
          finish = resolve
        }),
    )
    const pending = state.practice.submitPracticeAnswer('bool')
    state.plans.clearActivePlan()
    finish({
      id: 'attempt',
      assignment_id: assignment.id,
      answer: 'bool',
      score: 100,
      is_correct: true,
      hint_used: false,
      created_at: '2026-10-14T12:00:00',
    })
    await pending
    expect(state.practice.attempts).toEqual([])
    expect(state.practice.lastAttemptFeedback).toBe('')
    expect(state.practice.actionLoading).toBe(false)
  })

  it('preserves successful analytics responses when one endpoint fails', async () => {
    const state = setup()
    await state.plans.loadPlan()
    state.analyticsApi.getSkills.mockRejectedValue(new Error('skills offline'))
    await state.analytics.loadAnalytics()
    expect(state.analytics.overview.progress).toBe(50)
    expect(state.analytics.overview.streakDays).toBe(2)
    expect(state.analytics.error).toContain('skills offline')
    expect(state.analytics.loading).toBe(false)
  })
})

describe('plan snapshot storage', () => {
  function storageAdapter() {
    const values = new Map<string, string>()
    const storage = new BrowserPlanStorage(() => ({
      getItem: (key) => values.get(key) ?? null,
      setItem: (key, value) => {
        values.set(key, value)
      },
      removeItem: (key) => {
        values.delete(key)
      },
    }))
    return { values, storage }
  }

  it('round trips a versioned plan independently of the store', () => {
    const { values, storage } = storageAdapter()
    expect(storage.write(savedPlan)).toBe(true)
    expect(JSON.parse(values.get(PLAN_STORAGE_KEY)!).version).toBe(2)
    expect(storage.read()).toEqual(savedPlan)
    storage.clear()
    expect(storage.read()).toBeNull()
  })

  it.each(['broken json', 'null', '{"version":1}', '{"version":2,"plan":{}}'])(
    'discards invalid snapshot %s',
    (raw) => {
      const { values, storage } = storageAdapter()
      values.set(PLAN_STORAGE_KEY, raw)
      expect(storage.read()).toBeNull()
      expect(values.has(PLAN_STORAGE_KEY)).toBe(false)
    },
  )

  it('handles unavailable browser storage', () => {
    const storage = new BrowserPlanStorage(() => {
      throw new Error('Access denied')
    })
    expect(storage.read()).toBeNull()
    expect(storage.write(savedPlan)).toBe(false)
    expect(() => storage.clear()).not.toThrow()
  })
})
