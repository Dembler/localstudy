export {
  ApiError,
  API_BASE_URL,
  apiRequest,
  isApiError,
  type ApiErrorPayload,
  type ApiRequestOptions,
  type QueryValue,
} from './client'

export {
  catalogApi,
  getCourse,
  getCoursePrerequisites,
  getLessonPreview,
  listCourses,
  searchCourses,
} from './catalog'
export {
  addPlanGoal,
  createPlan,
  getPlanForecast,
  plansApi,
  rebalancePlan,
  updatePlanWorkload,
} from './plans'
export {
  completeSession,
  getSessionCalendar,
  rescheduleSession,
  scheduleSession,
  sessionsApi,
  startSession,
} from './sessions'
export {
  getNextAssignment,
  listAttempts,
  practiceApi,
  requestHint,
  retryAssignment,
  submitAttempt,
} from './practice'
export {
  analyticsApi,
  getOverview,
  getRecommendations,
  getSkills,
  getStreak,
  getWeakTopics,
} from './analytics'
export { getHealth, healthApi } from './health'
export type * from './types'
