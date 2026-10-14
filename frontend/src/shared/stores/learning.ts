import { acceptHMRUpdate, defineStore } from 'pinia'
import { computed, ref } from 'vue'

import {
  analyticsApi,
  catalogApi,
  isApiError,
  plansApi,
  practiceApi,
  sessionsApi,
  type CourseSummary,
  type PracticeAssignment,
  type PracticeAttempt,
  type StudyPlan,
  type StudySession,
} from '@/shared/api'
import {
  demoCourses,
  type UiAssignment,
  type UiAttempt,
  type UiCourse,
  type UiPlan,
  type UiRecommendation,
  type UiSession,
  type UiSkill,
} from '@/shared/data/demo'

interface AnalyticsOverviewView {
  progress: number
  studiedMinutes: number
  completedSessions: number
  streakDays: number
}

interface WeakTopicView {
  id: string
  title: string
  reason: string
  score: number
}

interface StoredPlanSnapshot {
  version: 2
  plan: UiPlan
}

type LoadingKey =
  | 'plan'
  | 'planAction'
  | 'catalog'
  | 'catalogAction'
  | 'sessions'
  | 'sessionAction'
  | 'practice'
  | 'practiceAction'
  | 'analytics'
type SectionKey = 'plan' | 'catalog' | 'sessions' | 'practice' | 'analytics'

const levelLabels: Record<CourseSummary['level'], string> = {
  beginner: 'Начальный',
  intermediate: 'Средний',
  advanced: 'Продвинутый',
}

const PLAN_STORAGE_KEY = 'localstudy.active-plan.v2'
const LEGACY_PLAN_STORAGE_KEY = 'localstudy.active-plan.v1'

function removeLegacyPlanSnapshot() {
  localStorage.removeItem(LEGACY_PLAN_STORAGE_KEY)
}

function readPlanSnapshot(): UiPlan | null {
  try {
    removeLegacyPlanSnapshot()
    const raw = localStorage.getItem(PLAN_STORAGE_KEY)
    if (!raw) return null
    const snapshot = JSON.parse(raw) as Partial<StoredPlanSnapshot>
    if (
      snapshot.version !== 2 ||
      !snapshot.plan?.id ||
      !snapshot.plan.title ||
      typeof snapshot.plan.courseId !== 'string' ||
      !snapshot.plan.courseId ||
      typeof snapshot.plan.weeklyMinutes !== 'number' ||
      !Array.isArray(snapshot.plan.milestones)
    ) {
      localStorage.removeItem(PLAN_STORAGE_KEY)
      return null
    }
    return snapshot.plan
  } catch {
    localStorage.removeItem(PLAN_STORAGE_KEY)
    return null
  }
}

function writePlanSnapshot(plan: UiPlan): boolean {
  try {
    const snapshot: StoredPlanSnapshot = { version: 2, plan }
    localStorage.setItem(PLAN_STORAGE_KEY, JSON.stringify(snapshot))
    removeLegacyPlanSnapshot()
    return true
  } catch {
    return false
  }
}

function clone<T>(value: T): T {
  return structuredClone(value)
}

function localDateTimeString(value: Date): string {
  const pad = (part: number) => String(part).padStart(2, '0')
  return [
    `${value.getFullYear()}-${pad(value.getMonth() + 1)}-${pad(value.getDate())}`,
    `${pad(value.getHours())}:${pad(value.getMinutes())}:${pad(value.getSeconds())}`,
  ].join('T')
}

function errorMessage(error: unknown): string {
  if (isApiError(error)) {
    if (error.status === 0) return error.message
    if (error.status === 404)
      return 'Нужные данные не найдены. Обновите страницу и попробуйте ещё раз.'
    if (error.status === 422) return 'Проверьте заполненные данные и попробуйте ещё раз.'
    return 'Не удалось выполнить действие. Попробуйте ещё раз.'
  }
  return error instanceof Error ? error.message : 'Произошла неизвестная ошибка.'
}

function planNameFromCourse(title: string): string {
  const normalized = title.trim().length >= 2 ? title.trim() : 'Учебный курс'
  const characters = Array.from(normalized)
  return characters.length <= 80 ? normalized : `${characters.slice(0, 79).join('').trimEnd()}…`
}

function normalizeCourse(course: CourseSummary): UiCourse {
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

function normalizePlan(plan: StudyPlan, previous?: UiPlan | null, targetCourseId?: string): UiPlan {
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

function normalizeSession(session: StudySession, courseTitle: string): UiSession {
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

function normalizeAssignment(item: PracticeAssignment): UiAssignment {
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

function normalizeAttempt(item: PracticeAttempt): UiAttempt {
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

export const useLearningWorkspaceStore = defineStore('learning-workspace', () => {
  const courses = ref<UiCourse[]>([])
  const selectedCourseId = ref<string | null>(null)
  const plan = ref<UiPlan | null>(null)
  const sessions = ref<UiSession[]>([])
  const selectedSessionId = ref<string | null>(null)
  const assignment = ref<UiAssignment | null>(null)
  const attempts = ref<UiAttempt[]>([])
  const visibleHint = ref('')
  const lastAttemptFeedback = ref('')
  const overview = ref<AnalyticsOverviewView>({
    progress: 0,
    studiedMinutes: 0,
    completedSessions: 0,
    streakDays: 0,
  })
  const skills = ref<UiSkill[]>([])
  const weakTopics = ref<WeakTopicView[]>([])
  const recommendations = ref<UiRecommendation[]>([])
  const loading = ref<Record<LoadingKey, boolean>>({
    plan: false,
    planAction: false,
    catalog: false,
    catalogAction: false,
    sessions: false,
    sessionAction: false,
    practice: false,
    practiceAction: false,
    analytics: false,
  })
  const errors = ref<Record<SectionKey, string>>({
    plan: '',
    catalog: '',
    sessions: '',
    practice: '',
    analytics: '',
  })
  const demoMode = ref<Record<SectionKey, boolean>>({
    plan: false,
    catalog: false,
    sessions: false,
    practice: false,
    analytics: false,
  })
  const actionMessage = ref('')

  const selectedCourse = computed(
    () =>
      courses.value.find((item) => item.id === selectedCourseId.value) ?? courses.value[0] ?? null,
  )

  function setFallback(section: SectionKey, error: unknown) {
    errors.value[section] = errorMessage(error)
    demoMode.value[section] = true
  }

  function setActionMessage(message: string) {
    actionMessage.value = message
  }

  function clearActionMessage() {
    actionMessage.value = ''
  }

  async function loadPlan() {
    loading.value.plan = true
    errors.value.plan = ''
    try {
      if (
        localStorage.getItem(LEGACY_PLAN_STORAGE_KEY) &&
        !localStorage.getItem(PLAN_STORAGE_KEY)
      ) {
        clearActivePlan()
      }
      if (plan.value) return
      const stored = readPlanSnapshot()
      if (!stored) return

      plan.value = stored
      try {
        const forecast = await plansApi.getPlanForecast(stored.id)
        plan.value.forecastDate = new Intl.DateTimeFormat('ru-RU', {
          day: 'numeric',
          month: 'long',
        }).format(new Date(forecast.expected_completion))
        plan.value.weeklyMinutes = forecast.weekly_minutes
        writePlanSnapshot(plan.value)
      } catch (error) {
        if (isApiError(error) && error.status === 404) {
          plan.value = null
          localStorage.removeItem(PLAN_STORAGE_KEY)
          return
        }
        errors.value.plan = 'Не удалось обновить прогноз. Сохранённый план всё ещё доступен.'
      }
    } finally {
      loading.value.plan = false
    }
  }

  async function createNewPlan(input: { weeklyMinutes: number; courseId: string }) {
    loading.value.planAction = true
    errors.value.plan = ''
    try {
      const courseId = input.courseId
      if (!courseId) throw new Error('В каталоге нет курса для первого учебного плана')
      const course = courses.value.find((item) => item.id === courseId)
      if (!course) throw new Error('Выбранный курс не найден в каталоге')

      const created = await plansApi.createPlan({
        name: planNameFromCourse(course.title),
        weekly_minutes: input.weeklyMinutes,
        course_ids: [courseId],
      })
      plan.value = normalizePlan(created, plan.value, courseId)
      demoMode.value.plan = false
      const persisted = writePlanSnapshot(plan.value)
      try {
        const forecast = await plansApi.getPlanForecast(created.id)
        plan.value.forecastDate = new Intl.DateTimeFormat('ru-RU', {
          day: 'numeric',
          month: 'long',
        }).format(new Date(forecast.expected_completion))
        writePlanSnapshot(plan.value)
      } catch {
        // The plan itself already exists; forecast refresh is non-blocking.
      }
      setActionMessage(
        persisted
          ? 'План создан. Теперь выберите время первого занятия.'
          : 'План создан, но браузер не смог сохранить его для следующего открытия.',
      )
      return true
    } catch (error) {
      errors.value.plan = errorMessage(error)
      setActionMessage('План не создан. Проверьте данные и попробуйте ещё раз.')
      return false
    } finally {
      loading.value.planAction = false
    }
  }

  function clearActivePlan() {
    plan.value = null
    sessions.value = []
    selectedSessionId.value = null
    assignment.value = null
    attempts.value = []
    errors.value.plan = ''
    actionMessage.value = ''
    localStorage.removeItem(PLAN_STORAGE_KEY)
    removeLegacyPlanSnapshot()
  }

  async function updateWorkload(weeklyMinutes: number) {
    if (!plan.value) return
    loading.value.planAction = true
    errors.value.plan = ''
    try {
      if (demoMode.value.plan) throw new Error('Демонстрационный режим')
      const updated = await plansApi.updatePlanWorkload(plan.value.id, {
        weekly_minutes: weeklyMinutes,
      })
      plan.value = normalizePlan(updated, plan.value)
      writePlanSnapshot(plan.value)
      setActionMessage('Недельная нагрузка обновлена.')
    } catch (error) {
      errors.value.plan = errorMessage(error)
      setActionMessage('Не удалось изменить нагрузку. Попробуйте ещё раз.')
    } finally {
      loading.value.planAction = false
    }
  }

  async function rebalanceCurrentPlan() {
    if (!plan.value) return
    loading.value.planAction = true
    errors.value.plan = ''
    try {
      if (demoMode.value.plan) throw new Error('Демонстрационный режим')
      const result = await plansApi.rebalancePlan(plan.value.id)
      plan.value.weeklyMinutes = result.weekly_minutes
      writePlanSnapshot(plan.value)
      await loadSessions()
      setActionMessage(result.message || 'План перестроен с учётом текущей нагрузки.')
    } catch (error) {
      errors.value.plan = errorMessage(error)
      setActionMessage('Не удалось перестроить план. Текущая версия сохранена.')
    } finally {
      loading.value.planAction = false
    }
  }

  async function loadCatalog() {
    loading.value.catalog = true
    errors.value.catalog = ''
    try {
      const result = await catalogApi.listCourses()
      courses.value = result.items.map(normalizeCourse)
      selectedCourseId.value = courses.value[0]?.id ?? null
      demoMode.value.catalog = false
    } catch (error) {
      setFallback('catalog', error)
      courses.value = clone(demoCourses)
      selectedCourseId.value = courses.value[0]?.id ?? null
    } finally {
      loading.value.catalog = false
    }
  }

  async function searchCatalog(query: string) {
    if (!query.trim() || demoMode.value.catalog) return
    loading.value.catalog = true
    try {
      const result = await catalogApi.searchCourses({ query })
      courses.value = result.items.map(normalizeCourse)
      selectedCourseId.value = courses.value[0]?.id ?? null
    } catch (error) {
      errors.value.catalog = errorMessage(error)
    } finally {
      loading.value.catalog = false
    }
  }

  async function selectCourse(courseId: string) {
    selectedCourseId.value = courseId
    if (demoMode.value.catalog) return
    try {
      const detail = await catalogApi.getCourse(courseId)
      const normalized = normalizeCourse(detail)
      normalized.skills = detail.skills
      courses.value = courses.value.map((item) => (item.id === courseId ? normalized : item))
    } catch (error) {
      errors.value.catalog = errorMessage(error)
    }
  }

  async function addSelectedCourseToPlan() {
    if (!selectedCourse.value) return
    loading.value.catalogAction = true
    errors.value.catalog = ''
    try {
      if (!plan.value || demoMode.value.plan)
        throw new Error('План пока работает в демонстрационном режиме')
      const targetDate = new Date()
      targetDate.setDate(targetDate.getDate() + 30)
      await plansApi.addPlanGoal(plan.value.id, {
        title: `Пройти курс «${selectedCourse.value.title}»`,
        target_date: targetDate.toISOString().slice(0, 10),
        target_minutes: selectedCourse.value.durationHours * 60,
      })
      setActionMessage(`Цель по курсу «${selectedCourse.value.title}» сохранена.`)
      return true
    } catch (error) {
      errors.value.catalog = errorMessage(error)
      setActionMessage('Не удалось сделать курс целью. Попробуйте ещё раз.')
      return false
    } finally {
      loading.value.catalogAction = false
    }
  }

  async function loadSessions() {
    loading.value.sessions = true
    errors.value.sessions = ''
    try {
      const end = new Date()
      end.setFullYear(end.getFullYear() + 2)
      const calendar = await sessionsApi.getSessionCalendar({
        from_date: plan.value?.startDate ?? '2000-01-01',
        to_date: end.toISOString().slice(0, 10),
      })
      sessions.value = calendar.items
        .filter((item) => item.plan_id === plan.value?.id)
        .map((item) => normalizeSession(item, plan.value?.title ?? 'Текущий план'))
      const nearestUnfinished = [...sessions.value]
        .filter((item) => item.status === 'scheduled' || item.status === 'in_progress')
        .sort((a, b) => {
          if (a.status === 'in_progress' && b.status !== 'in_progress') return -1
          if (b.status === 'in_progress' && a.status !== 'in_progress') return 1
          return Date.parse(a.startsAt) - Date.parse(b.startsAt)
        })[0]
      selectedSessionId.value = nearestUnfinished?.id ?? null
      demoMode.value.sessions = false
    } catch (error) {
      errors.value.sessions = errorMessage(error)
      sessions.value = []
      selectedSessionId.value = null
      demoMode.value.sessions = false
    } finally {
      loading.value.sessions = false
    }
  }

  function selectSession(sessionId: string) {
    selectedSessionId.value = sessionId
  }

  async function advanceSession(sessionId: string) {
    const current = sessions.value.find((item) => item.id === sessionId)
    if (!current) return
    loading.value.sessionAction = true
    errors.value.sessions = ''
    try {
      if (demoMode.value.sessions) throw new Error('Демонстрационный режим')
      const updated =
        current.status === 'scheduled'
          ? await sessionsApi.startSession(sessionId)
          : await sessionsApi.completeSession(sessionId, { score: null })
      const normalized = normalizeSession(updated, current.courseTitle)
      sessions.value = sessions.value.map((item) => (item.id === sessionId ? normalized : item))
      if (normalized.status === 'completed' && plan.value) {
        plan.value.hasActivity = true
        writePlanSnapshot(plan.value)
      }
      setActionMessage(
        normalized.status === 'in_progress'
          ? 'Занятие началось. Удачной работы!'
          : 'Занятие завершено и учтено в прогрессе.',
      )
      const next =
        sessions.value.find((item) => item.status === 'in_progress') ??
        sessions.value.find((item) => item.status === 'scheduled')
      selectedSessionId.value = next?.id ?? null
    } catch (error) {
      errors.value.sessions = errorMessage(error)
      setActionMessage('Не удалось изменить статус занятия. Попробуйте ещё раз.')
    } finally {
      loading.value.sessionAction = false
    }
  }

  async function scheduleLearningSession(value: string) {
    if (!plan.value) {
      errors.value.sessions = 'Сначала настройте учебный план.'
      return
    }
    loading.value.sessionAction = true
    errors.value.sessions = ''
    const scheduledAt = value
    try {
      if (demoMode.value.sessions) throw new Error('Демонстрационный режим')
      let lessonId = assignment.value?.lessonId
      if (!lessonId) {
        const next = await practiceApi.getNextAssignment({
          plan_id: plan.value.id,
          course_id: plan.value.courseId,
        })
        assignment.value = normalizeAssignment(next)
        lessonId = next.lesson_id
      }
      const created = await sessionsApi.scheduleSession({
        plan_id: plan.value.id,
        lesson_id: lessonId,
        scheduled_for: scheduledAt,
        duration_minutes: 45,
      })
      sessions.value.push(normalizeSession(created, plan.value.title))
      sessions.value.sort((a, b) => Date.parse(a.startsAt) - Date.parse(b.startsAt))
      const nearest =
        sessions.value.find((item) => item.status === 'in_progress') ??
        sessions.value.find((item) => item.status === 'scheduled')
      selectedSessionId.value = nearest?.id ?? null
      setActionMessage('Занятие добавлено в расписание.')
    } catch (error) {
      errors.value.sessions = errorMessage(error)
      setActionMessage('Не удалось добавить занятие. Выберите другое время и попробуйте ещё раз.')
    } finally {
      loading.value.sessionAction = false
    }
  }

  async function rescheduleSelectedSession() {
    const current = sessions.value.find((item) => item.id === selectedSessionId.value)
    if (!current) return
    loading.value.sessionAction = true
    errors.value.sessions = ''
    const nextDate = new Date(current.startsAt)
    nextDate.setDate(nextDate.getDate() + 1)
    try {
      if (demoMode.value.sessions) throw new Error('Демонстрационный режим')
      const updated = await sessionsApi.rescheduleSession(current.id, {
        scheduled_for: localDateTimeString(nextDate),
      })
      Object.assign(current, normalizeSession(updated, current.courseTitle))
      setActionMessage('Занятие перенесено на завтра.')
    } catch (error) {
      errors.value.sessions = errorMessage(error)
      setActionMessage('Не удалось перенести занятие. Попробуйте ещё раз.')
    } finally {
      loading.value.sessionAction = false
    }
  }

  async function loadPractice() {
    if (!plan.value) {
      assignment.value = null
      attempts.value = []
      return
    }
    loading.value.practice = true
    errors.value.practice = ''
    try {
      const item = await practiceApi.getNextAssignment({
        plan_id: plan.value.id,
        course_id: plan.value.courseId,
      })
      assignment.value = normalizeAssignment(item)
      const history = await practiceApi.listAttempts(item.id)
      attempts.value = history.items.map(normalizeAttempt)
      demoMode.value.practice = false
    } catch (error) {
      errors.value.practice = errorMessage(error)
      assignment.value = null
      attempts.value = []
      demoMode.value.practice = false
    } finally {
      loading.value.practice = false
    }
  }

  async function submitPracticeAnswer(answer: string) {
    if (!assignment.value) return
    loading.value.practiceAction = true
    errors.value.practice = ''
    try {
      if (demoMode.value.practice) throw new Error('Демонстрационный режим')
      const result = await practiceApi.submitAttempt(assignment.value.id, { answer })
      const normalized = normalizeAttempt(result)
      attempts.value.unshift(normalized)
      lastAttemptFeedback.value = normalized.feedback
      if (plan.value) {
        plan.value.hasActivity = true
        writePlanSnapshot(plan.value)
      }
      setActionMessage('Ответ отправлен и проверен.')
    } catch (error) {
      errors.value.practice = errorMessage(error)
      setActionMessage('Ответ не отправлен. Ваш текст остался в форме — попробуйте ещё раз.')
    } finally {
      loading.value.practiceAction = false
    }
  }

  async function requestPracticeHint() {
    if (!assignment.value) return
    loading.value.practiceAction = true
    errors.value.practice = ''
    try {
      if (demoMode.value.practice) throw new Error('Демонстрационный режим')
      const hint = await practiceApi.requestHint(assignment.value.id)
      visibleHint.value = hint.hint
    } catch (error) {
      errors.value.practice = errorMessage(error)
      setActionMessage('Не удалось получить подсказку. Попробуйте ещё раз.')
    } finally {
      loading.value.practiceAction = false
    }
  }

  async function retryPracticeAssignment() {
    if (!assignment.value) return
    loading.value.practiceAction = true
    errors.value.practice = ''
    try {
      if (demoMode.value.practice) throw new Error('Демонстрационный режим')
      const next = await practiceApi.retryAssignment(assignment.value.id)
      assignment.value = normalizeAssignment(next.assignment)
      visibleHint.value = ''
      lastAttemptFeedback.value = ''
      setActionMessage('Новая попытка готова. Условие задания осталось прежним.')
    } catch (error) {
      errors.value.practice = errorMessage(error)
      setActionMessage('Не удалось подготовить повтор. Попробуйте ещё раз.')
    } finally {
      loading.value.practiceAction = false
    }
  }

  async function loadAnalytics() {
    loading.value.analytics = true
    errors.value.analytics = ''
    const results = await Promise.allSettled([
      analyticsApi.getOverview(),
      analyticsApi.getSkills(),
      analyticsApi.getStreak(),
      analyticsApi.getWeakTopics(),
      analyticsApi.getRecommendations(),
    ])
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

    if (failed) errors.value.analytics = errorMessage(failed.reason)
    demoMode.value.analytics = false
    loading.value.analytics = false
  }

  return {
    courses,
    selectedCourse,
    plan,
    sessions,
    selectedSessionId,
    assignment,
    attempts,
    visibleHint,
    lastAttemptFeedback,
    overview,
    skills,
    weakTopics,
    recommendations,
    loading,
    errors,
    demoMode,
    actionMessage,
    clearActionMessage,
    loadPlan,
    createNewPlan,
    clearActivePlan,
    updateWorkload,
    rebalanceCurrentPlan,
    loadCatalog,
    searchCatalog,
    selectCourse,
    addSelectedCourseToPlan,
    loadSessions,
    selectSession,
    advanceSession,
    scheduleLearningSession,
    rescheduleSelectedSession,
    loadPractice,
    submitPracticeAnswer,
    requestPracticeHint,
    retryPracticeAssignment,
    loadAnalytics,
  }
})

if (import.meta.hot) {
  import.meta.hot.accept(acceptHMRUpdate(useLearningWorkspaceStore, import.meta.hot))
}
