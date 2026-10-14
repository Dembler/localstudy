import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usePlanScope } from './plan-scope'
import { errorMessage } from '@/shared/presentation/errors'
import { useNoticesStore } from './notices'
import { usePlanStore } from './plans'
import { PRACTICE_GATEWAY, useDependency } from '@/shared/services/ports'
import { normalizeAssignment, normalizeAttempt } from '@/shared/presentation/practice'
import type { UiAssignment, UiAttempt } from '@/shared/types/learning'

export const usePracticeStore = defineStore('practice', () => {
  const practiceApi = useDependency(PRACTICE_GATEWAY)
  const plans = usePlanStore()
  const notices = useNoticesStore()
  const assignment = ref<UiAssignment | null>(null)
  const attempts = ref<UiAttempt[]>([])
  const visibleHint = ref('')
  const lastAttemptFeedback = ref('')
  const loading = ref(false)
  const actionLoading = ref(false)
  const error = ref('')
  function reset() {
    assignment.value = null
    attempts.value = []
    visibleHint.value = ''
    lastAttemptFeedback.value = ''
    error.value = ''
    loading.value = false
    actionLoading.value = false
  }
  const captureScope = usePlanScope(() => plans.plan?.id, reset)

  async function loadPractice() {
    const isCurrent = captureScope()
    if (!plans.plan) {
      assignment.value = null
      attempts.value = []
      return
    }
    visibleHint.value = ''
    lastAttemptFeedback.value = ''
    loading.value = true
    error.value = ''
    try {
      const item = await practiceApi.getNextAssignment({
        plan_id: plans.plan.id,
        course_id: plans.plan.courseId,
      })
      if (!isCurrent()) return
      const history = await practiceApi.listAttempts(item.id)
      if (!isCurrent()) return
      assignment.value = normalizeAssignment(item)
      attempts.value = history.items.map(normalizeAttempt)
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      assignment.value = null
      attempts.value = []
    } finally {
      if (isCurrent()) {
        loading.value = false
      }
    }
  }

  async function submitPracticeAnswer(answer: string) {
    const isCurrent = captureScope()
    if (!assignment.value) return
    actionLoading.value = true
    error.value = ''
    try {
      const result = await practiceApi.submitAttempt(assignment.value.id, { answer })
      if (!isCurrent()) return
      const normalized = normalizeAttempt(result)
      attempts.value.unshift(normalized)
      lastAttemptFeedback.value = normalized.feedback
      if (plans.plan) {
        plans.markActivity()
      }
      notices.setMessage('Ответ отправлен и проверен.')
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Ответ не отправлен. Ваш текст остался в форме — попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  async function requestPracticeHint() {
    const isCurrent = captureScope()
    if (!assignment.value) return
    actionLoading.value = true
    error.value = ''
    try {
      const hint = await practiceApi.requestHint(assignment.value.id)
      if (!isCurrent()) return
      visibleHint.value = hint.hint
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось получить подсказку. Попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  async function retryPracticeAssignment() {
    const isCurrent = captureScope()
    if (!assignment.value) return
    actionLoading.value = true
    error.value = ''
    try {
      const next = await practiceApi.retryAssignment(assignment.value.id)
      if (!isCurrent()) return
      assignment.value = normalizeAssignment(next.assignment)
      visibleHint.value = ''
      lastAttemptFeedback.value = ''
      notices.setMessage('Новая попытка готова. Условие задания осталось прежним.')
    } catch (cause) {
      if (!isCurrent()) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось подготовить повтор. Попробуйте ещё раз.')
    } finally {
      if (isCurrent()) {
        actionLoading.value = false
      }
    }
  }

  async function getLessonForSession(): Promise<string | null> {
    if (assignment.value) return assignment.value.lessonId
    const plan = plans.plan
    if (!plan) return null
    const isCurrent = captureScope()
    const next = await practiceApi.getNextAssignment({ plan_id: plan.id, course_id: plan.courseId })
    if (!isCurrent()) return null
    assignment.value = normalizeAssignment(next)
    return next.lesson_id
  }

  return {
    assignment,
    attempts,
    visibleHint,
    lastAttemptFeedback,
    loading,
    actionLoading,
    error,
    getLessonForSession,
    loadPractice,
    submitPracticeAnswer,
    requestPracticeHint,
    retryPracticeAssignment,
  }
})
