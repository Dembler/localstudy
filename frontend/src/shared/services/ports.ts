import { inject, type InjectionKey } from 'vue'

import type {
  AddPlanGoalInput,
  AnalyticsOverview,
  CompleteSessionInput,
  CourseDetail,
  CourseList,
  CourseListParams,
  CourseSearchParams,
  CreatePlanInput,
  LearningStreak,
  NextAssignmentParams,
  PlanForecast,
  PlanGoal,
  PracticeAssignment,
  PracticeAttempt,
  PracticeAttemptHistory,
  PracticeHint,
  PracticeRetry,
  RebalanceResult,
  RecommendationList,
  RescheduleSessionInput,
  ScheduleSessionInput,
  SessionCalendar,
  SessionCalendarParams,
  SkillProgressList,
  StudyPlan,
  StudySession,
  SubmitAttemptInput,
  UpdateWorkloadInput,
  WeakTopicList,
} from '@/shared/api/types'
import type { UiPlan } from '@/shared/types/learning'

export interface CatalogGateway {
  listCourses(params?: CourseListParams): Promise<CourseList>
  searchCourses(params: CourseSearchParams): Promise<CourseList>
  getCourse(courseId: string): Promise<CourseDetail>
}

export interface PlansGateway {
  createPlan(input: CreatePlanInput): Promise<StudyPlan>
  updatePlanWorkload(planId: string, input: UpdateWorkloadInput): Promise<StudyPlan>
  addPlanGoal(planId: string, input: AddPlanGoalInput): Promise<PlanGoal>
  rebalancePlan(planId: string): Promise<RebalanceResult>
  getPlanForecast(planId: string): Promise<PlanForecast>
  deletePlan(planId: string): Promise<void>
  deletePlanGoal(planId: string, goalId: string): Promise<void>
  removePlanCourse(planId: string, courseId: string): Promise<void>
}

export interface SessionsGateway {
  getSessionCalendar(params?: SessionCalendarParams): Promise<SessionCalendar>
  scheduleSession(input: ScheduleSessionInput): Promise<StudySession>
  startSession(sessionId: string): Promise<StudySession>
  completeSession(sessionId: string, input: CompleteSessionInput): Promise<StudySession>
  rescheduleSession(sessionId: string, input: RescheduleSessionInput): Promise<StudySession>
  deleteSession(sessionId: string): Promise<void>
}

export interface PracticeGateway {
  getNextAssignment(params: NextAssignmentParams): Promise<PracticeAssignment>
  submitAttempt(assignmentId: string, input: SubmitAttemptInput): Promise<PracticeAttempt>
  requestHint(assignmentId: string): Promise<PracticeHint>
  retryAssignment(assignmentId: string): Promise<PracticeRetry>
  listAttempts(assignmentId: string): Promise<PracticeAttemptHistory>
}

export interface AnalyticsGateway {
  getOverview(): Promise<AnalyticsOverview>
  getSkills(): Promise<SkillProgressList>
  getStreak(): Promise<LearningStreak>
  getWeakTopics(): Promise<WeakTopicList>
  getRecommendations(): Promise<RecommendationList>
}

export interface PlanStorage {
  read(): UiPlan | null
  write(plan: UiPlan): boolean
  clear(): void
}

export const CATALOG_GATEWAY: InjectionKey<CatalogGateway> = Symbol('catalog gateway')
export const PLANS_GATEWAY: InjectionKey<PlansGateway> = Symbol('plans gateway')
export const SESSIONS_GATEWAY: InjectionKey<SessionsGateway> = Symbol('sessions gateway')
export const PRACTICE_GATEWAY: InjectionKey<PracticeGateway> = Symbol('practice gateway')
export const ANALYTICS_GATEWAY: InjectionKey<AnalyticsGateway> = Symbol('analytics gateway')
export const PLAN_STORAGE: InjectionKey<PlanStorage> = Symbol('plan storage')

export function useDependency<T>(key: InjectionKey<T>): T {
  const dependency = inject(key)
  if (!dependency) throw new Error(`Missing application dependency: ${String(key)}`)
  return dependency
}
