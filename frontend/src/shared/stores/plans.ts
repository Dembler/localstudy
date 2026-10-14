import { defineStore } from 'pinia'
import { ref } from 'vue'

import { isApiError } from '@/shared/api/client'
import { errorMessage } from '@/shared/presentation/errors'
import { normalizePlan, planNameFromCourse } from '@/shared/presentation/plans'
import { PLANS_GATEWAY, PLAN_STORAGE, useDependency } from '@/shared/services/ports'
import type { UiCourse, UiPlan } from '@/shared/types/learning'
import { useNoticesStore } from './notices'

export const usePlanStore = defineStore('plans', () => {
  const api = useDependency(PLANS_GATEWAY)
  const storage = useDependency(PLAN_STORAGE)
  const notices = useNoticesStore()
  const plan = ref<UiPlan | null>(null)
  const loading = ref(false)
  const actionLoading = ref(false)
  const goalLoading = ref(false)
  const error = ref('')
  const goalError = ref('')

  async function refreshForecast() {
    if (!plan.value) return
    const planId = plan.value.id
    const forecast = await api.getPlanForecast(planId)
    if (plan.value?.id !== planId) return
    plan.value.forecastDate = new Intl.DateTimeFormat('ru-RU', {
      day: 'numeric',
      month: 'long',
    }).format(new Date(forecast.expected_completion))
    plan.value.weeklyMinutes = forecast.weekly_minutes
    storage.write(plan.value)
  }

  async function loadPlan() {
    if (plan.value) return
    loading.value = true
    error.value = ''
    try {
      plan.value = storage.read()
      if (!plan.value) return
      const planId = plan.value.id
      try {
        await refreshForecast()
      } catch (cause) {
        if (plan.value?.id !== planId) return
        if (isApiError(cause) && cause.status === 404) {
          clearActivePlan()
          return
        }
        error.value = 'Не удалось обновить прогноз. Сохранённый план всё ещё доступен.'
      }
    } finally {
      loading.value = false
    }
  }

  async function createNewPlan(input: { weeklyMinutes: number; course: UiCourse }) {
    actionLoading.value = true
    error.value = ''
    try {
      const created = await api.createPlan({
        name: planNameFromCourse(input.course.title),
        weekly_minutes: input.weeklyMinutes,
        course_ids: [input.course.id],
      })
      plan.value = normalizePlan(created, null, input.course.id)
      const persisted = storage.write(plan.value)
      try {
        await refreshForecast()
      } catch {
        /* The plan itself already exists. */
      }
      notices.setMessage(
        persisted
          ? 'План создан. Теперь выберите время первого занятия.'
          : 'План создан, но браузер не смог сохранить его для следующего открытия.',
      )
      return true
    } catch (cause) {
      error.value = errorMessage(cause)
      notices.setMessage('План не создан. Проверьте данные и попробуйте ещё раз.')
      return false
    } finally {
      actionLoading.value = false
    }
  }

  function clearActivePlan() {
    plan.value = null
    error.value = ''
    goalError.value = ''
    notices.clearActionMessage()
    storage.clear()
  }

  function markActivity() {
    if (!plan.value) return
    plan.value.hasActivity = true
    storage.write(plan.value)
  }

  async function updateWorkload(weeklyMinutes: number) {
    if (!plan.value) return
    const planId = plan.value.id
    actionLoading.value = true
    error.value = ''
    try {
      const updated = await api.updatePlanWorkload(planId, { weekly_minutes: weeklyMinutes })
      if (plan.value?.id !== planId) return
      plan.value = normalizePlan(updated, plan.value)
      storage.write(plan.value)
      notices.setMessage('Недельная нагрузка обновлена.')
    } catch (cause) {
      if (plan.value?.id !== planId) return
      error.value = errorMessage(cause)
      notices.setMessage('Не удалось изменить нагрузку. Попробуйте ещё раз.')
    } finally {
      actionLoading.value = false
    }
  }

  async function rebalanceCurrentPlan() {
    if (!plan.value) return false
    const planId = plan.value.id
    actionLoading.value = true
    error.value = ''
    try {
      const result = await api.rebalancePlan(planId)
      if (plan.value?.id !== planId) return false
      plan.value.weeklyMinutes = result.weekly_minutes
      storage.write(plan.value)
      notices.setMessage(result.message || 'План перестроен с учётом текущей нагрузки.')
      return true
    } catch (cause) {
      if (plan.value?.id === planId) {
        error.value = errorMessage(cause)
        notices.setMessage('Не удалось перестроить план. Текущая версия сохранена.')
      }
      return false
    } finally {
      actionLoading.value = false
    }
  }

  async function addCourseGoal(course: UiCourse) {
    if (!plan.value) return false
    goalLoading.value = true
    goalError.value = ''
    try {
      const targetDate = new Date()
      targetDate.setDate(targetDate.getDate() + 30)
      await api.addPlanGoal(plan.value.id, {
        title: `Пройти курс «${course.title}»`,
        target_date: targetDate.toISOString().slice(0, 10),
        target_minutes: course.durationHours * 60,
      })
      notices.setMessage(`Цель по курсу «${course.title}» сохранена.`)
      return true
    } catch (cause) {
      goalError.value = errorMessage(cause)
      notices.setMessage('Не удалось сделать курс целью. Попробуйте ещё раз.')
      return false
    } finally {
      goalLoading.value = false
    }
  }

  return {
    plan,
    loading,
    actionLoading,
    goalLoading,
    error,
    goalError,
    loadPlan,
    createNewPlan,
    clearActivePlan,
    markActivity,
    updateWorkload,
    rebalanceCurrentPlan,
    addCourseGoal,
  }
})
