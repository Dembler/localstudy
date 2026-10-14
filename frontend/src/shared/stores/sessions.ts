import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usePlanScope } from './plan-scope'
import { errorMessage } from '@/shared/presentation/errors'
import { useNoticesStore } from './notices'
import { usePlanStore } from './plans'
import { SESSIONS_GATEWAY, useDependency } from '@/shared/services/ports'
import { normalizeSession } from '@/shared/presentation/sessions'
import { localDateTimeString } from '@/shared/presentation/dates'
import type { UiSession } from '@/shared/types/learning'
import { usePracticeStore } from './practice'

export const useSessionsStore = defineStore('sessions', () => {
  const sessionsApi = useDependency(SESSIONS_GATEWAY)
  const plans = usePlanStore()
  const practice = usePracticeStore()
  const notices = useNoticesStore()
  const sessions = ref<UiSession[]>([])
  const selectedSessionId = ref<string | null>(null)
  const loading = ref(false)
  const actionLoading = ref(false)
  const error = ref('')

  function reset() {
    sessions.value = []
    selectedSessionId.value = null
    error.value = ''
    loading.value = false
    actionLoading.value = false
  }
  const captureScope = usePlanScope(() => plans.plan?.id, reset)

  async function loadSessions() {
    const isCurrent = captureScope()
    const planId = plans.plan?.id
    if (!planId) {
      reset()
      return
    }
    loading.value = true
    error.value = ''
    try {
      const end = new Date()
      end.setFullYear(end.getFullYear() + 2)
      const calendar = await sessionsApi.getSessionCalendar({
        from_date: plans.plan?.startDate ?? '2000-01-01',
        to_date: end.toISOString().slice(0, 10),
      })
      if (!isCurrent()) return
      sessions.value = calendar.items
        .filter((item) => item.plan_id === plans.plan?.id)
        .map((item) => normalizeSession(item, plans.plan?.title ?? 'Текущий план'))
      const nearestUnfinished = [...sessions.value]
        .filter((item) => item.status === 'scheduled' || item.status === 'in_progress')
        .sort((a, b) => {
          if (a.status === 'in_progress' && b.status !== 'in_progress') return -1
          if (b.status === 'in_progress' && a.status !== 'in_progress') return 1
          return Date.parse(a.startsAt) - Date.parse(b.startsAt)
        })[0]
      selectedSessionId.value = nearestUnfinished?.id ?? null
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      sessions.value = []
      selectedSessionId.value = null
    } finally {
      if (isCurrent()) {
        loading.value = false
      }
    }
  }

  function selectSession(sessionId: string) {
    selectedSessionId.value = sessionId
  }

  async function advanceSession(sessionId: string) {
    const isCurrent = captureScope()
    const current = sessions.value.find((item) => item.id === sessionId)
    if (!current) return
    actionLoading.value = true
    error.value = ''
    try {
      const updated =
        current.status === 'scheduled'
          ? await sessionsApi.startSession(sessionId)
          : await sessionsApi.completeSession(sessionId, { score: null })
      if (!isCurrent()) return
      const normalized = normalizeSession(updated, current.courseTitle)
      sessions.value = sessions.value.map((item) => (item.id === sessionId ? normalized : item))
      if (normalized.status === 'completed' && plans.plan) {
        plans.markActivity()
      }
      notices.setMessage(
        normalized.status === 'in_progress'
          ? 'Занятие началось. Удачной работы!'
          : 'Занятие завершено и учтено в прогрессе.',
      )
      const next =
        sessions.value.find((item) => item.status === 'in_progress') ??
        sessions.value.find((item) => item.status === 'scheduled')
      selectedSessionId.value = next?.id ?? null
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось изменить статус занятия. Попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  async function scheduleLearningSession(value: string) {
    const isCurrent = captureScope()
    if (!plans.plan) {
      error.value = 'Сначала настройте учебный план.'
      return
    }
    actionLoading.value = true
    error.value = ''
    const scheduledAt = value
    try {
      const lessonId = await practice.getLessonForSession()
      if (!isCurrent() || !lessonId || !plans.plan) return
      const created = await sessionsApi.scheduleSession({
        plan_id: plans.plan.id,
        lesson_id: lessonId,
        scheduled_for: scheduledAt,
        duration_minutes: 45,
      })
      if (!isCurrent() || !plans.plan) return
      sessions.value.push(normalizeSession(created, plans.plan.title))
      sessions.value.sort((a, b) => Date.parse(a.startsAt) - Date.parse(b.startsAt))
      const nearest =
        sessions.value.find((item) => item.status === 'in_progress') ??
        sessions.value.find((item) => item.status === 'scheduled')
      selectedSessionId.value = nearest?.id ?? null
      notices.setMessage('Занятие добавлено в расписание.')
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось добавить занятие. Выберите другое время и попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  async function rescheduleSelectedSession() {
    const isCurrent = captureScope()
    const current = sessions.value.find((item) => item.id === selectedSessionId.value)
    if (!current) return
    actionLoading.value = true
    error.value = ''
    const nextDate = new Date(current.startsAt)
    nextDate.setDate(nextDate.getDate() + 1)
    try {
      const updated = await sessionsApi.rescheduleSession(current.id, {
        scheduled_for: localDateTimeString(nextDate),
      })
      if (!isCurrent()) return
      Object.assign(current, normalizeSession(updated, current.courseTitle))
      notices.setMessage('Занятие перенесено на завтра.')
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось перенести занятие. Попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  return {
    sessions,
    selectedSessionId,
    loading,
    actionLoading,
    error,
    loadSessions,
    selectSession,
    advanceSession,
    scheduleLearningSession,
    rescheduleSelectedSession,
  }
})
