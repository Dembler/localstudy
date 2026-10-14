import { defineStore } from 'pinia'
import { ref } from 'vue'
import { usePlanScope } from './plan-scope'
import { errorMessage } from '@/shared/presentation/errors'
import { usePlanStore } from './plans'
import { ANALYTICS_GATEWAY, useDependency } from '@/shared/services/ports'
import type {
  AnalyticsOverviewView,
  WeakTopicView,
  UiSkill,
  UiRecommendation,
} from '@/shared/types/learning'

export const useAnalyticsStore = defineStore('analytics', () => {
  const analyticsApi = useDependency(ANALYTICS_GATEWAY)
  const plans = usePlanStore()
  const overview = ref<AnalyticsOverviewView>({
    progress: 0,
    studiedMinutes: 0,
    completedSessions: 0,
    streakDays: 0,
  })
  const skills = ref<UiSkill[]>([])
  const weakTopics = ref<WeakTopicView[]>([])
  const recommendations = ref<UiRecommendation[]>([])
  const loading = ref(false)
  const error = ref('')
  const demoMode = ref(false)
  function reset() {
    overview.value = { progress: 0, studiedMinutes: 0, completedSessions: 0, streakDays: 0 }
    skills.value = []
    weakTopics.value = []
    recommendations.value = []
    error.value = ''
    loading.value = false
  }
  const captureScope = usePlanScope(() => plans.plan?.id, reset)

  async function loadAnalytics() {
    const isCurrent = captureScope()
    const planId = plans.plan?.id
    if (!planId) {
      reset()
      return
    }
    loading.value = true
    error.value = ''
    const results = await Promise.allSettled([
      analyticsApi.getOverview(),
      analyticsApi.getSkills(),
      analyticsApi.getStreak(),
      analyticsApi.getWeakTopics(),
      analyticsApi.getRecommendations(),
    ])
    if (!isCurrent()) return
    const failed = results.find((result) => result.status === 'rejected')

    if (results[0].status === 'fulfilled') {
      const item = results[0].value
      overview.value = {
        progress: item.completion_percent,
        studiedMinutes: item.study_minutes,
        completedSessions: item.completed_sessions,
        streakDays: 0,
      }
    }
    if (results[1].status === 'fulfilled') {
      skills.value = results[1].value.items.map((item) => ({
        id: item.skill,
        name: item.skill,
        value: item.progress_percent,
        trend: item.level === 'advanced' ? 6 : item.level === 'beginner' ? -3 : 0,
      }))
    }
    if (results[2].status === 'fulfilled') overview.value.streakDays = results[2].value.current_days
    if (results[3].status === 'fulfilled') {
      weakTopics.value = results[3].value.items.map((item) => ({
        id: item.topic,
        title: item.topic,
        score: item.average_score,
        reason: `${item.attempts} попытки · ${item.suggested_action}`,
      }))
    }
    if (results[4].status === 'fulfilled') {
      recommendations.value = results[4].value.items.map((item) => ({
        id: item.action_id ?? `${item.kind}-${item.title}`,
        title: item.title,
        reason: item.reason,
        topic: item.kind === 'practice' ? 'Практическое задание' : 'Следующий шаг',
        estimatedMinutes: 20,
        to: item.kind === 'schedule' ? '/sessions' : '/practice',
      }))
    }

    if (failed) error.value = errorMessage(failed.reason)
    demoMode.value = false
    loading.value = false
  }

  return { overview, skills, weakTopics, recommendations, loading, error, demoMode, loadAnalytics }
})
