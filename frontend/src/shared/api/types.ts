export type EntityId = string
export type IsoDate = string
export type IsoDateTime = string

export type CourseLevel = 'beginner' | 'intermediate' | 'advanced'

export interface ItemCollection<T> {
  items: T[]
}

export interface ListResult<T> extends ItemCollection<T> {
  total: number
}

export interface CourseSummary {
  id: EntityId
  slug: string
  title: string
  description: string
  level: CourseLevel
  duration_minutes: number
  skills: string[]
  lesson_count: number
}

export interface CourseSearchParams {
  query: string
}

export interface CourseListParams {
  level?: CourseLevel
  skill?: string
}

export type CourseList = ListResult<CourseSummary>

export interface CourseDetail extends CourseSummary {
  prerequisite_ids: EntityId[]
}

export interface LessonPreview {
  id: EntityId
  course_id: EntityId
  title: string
  summary: string
  preview: string
  duration_minutes: number
  position: number
}

export interface CreatePlanInput {
  name: string
  weekly_minutes: number
  start_date?: IsoDate
  course_ids: EntityId[]
}

export interface UpdateWorkloadInput {
  weekly_minutes: number
}

export interface AddPlanGoalInput {
  title: string
  target_date: IsoDate
  target_minutes: number
}

export interface StudyPlan {
  id: EntityId
  name: string
  weekly_minutes: number
  start_date: IsoDate
  course_ids: EntityId[]
  created_at: IsoDateTime
}

export interface PlanGoal {
  id: EntityId
  plan_id: EntityId
  title: string
  target_date: IsoDate
  target_minutes: number
  progress_percent: number
}

export interface RebalanceResult {
  plan_id: EntityId
  sessions_updated: number
  weekly_minutes: number
  message: string
}

export interface PlanForecast {
  plan_id: EntityId
  remaining_minutes: number
  weekly_minutes: number
  expected_completion: IsoDate
  weeks_remaining: number
  confidence: string
}

export type SessionStatus = 'planned' | 'in_progress' | 'completed' | 'cancelled'

export interface StudySession {
  id: EntityId
  plan_id: EntityId
  lesson_id: EntityId
  lesson_title: string
  scheduled_for: IsoDateTime
  duration_minutes: number
  status: SessionStatus
  started_at: IsoDateTime | null
  completed_at: IsoDateTime | null
  score: number | null
}

export interface SessionCalendarParams {
  from_date?: IsoDate
  to_date?: IsoDate
}

export interface NextAssignmentParams {
  plan_id: EntityId
  course_id?: EntityId
}

export interface SessionCalendar extends ListResult<StudySession> {
  from_date: IsoDate
  to_date: IsoDate
}

export interface ScheduleSessionInput {
  plan_id: EntityId
  lesson_id: EntityId
  scheduled_for: IsoDateTime
  duration_minutes: number
}

export interface CompleteSessionInput {
  score?: number | null
}

export interface RescheduleSessionInput {
  scheduled_for: IsoDateTime
}

export interface PracticeAssignment {
  id: EntityId
  lesson_id: EntityId
  topic: string
  prompt: string
  difficulty: number
  attempts_count: number
}

export interface SubmitAttemptInput {
  answer: string
}

export interface PracticeAttempt {
  id: EntityId
  assignment_id: EntityId
  answer: string
  is_correct: boolean
  score: number
  hint_used: boolean
  created_at: IsoDateTime
}

export interface PracticeHint {
  assignment_id: EntityId
  hint: string
  penalty_percent: number
}

export interface PracticeRetry {
  assignment: PracticeAssignment
  previous_best_score: number
  message: string
}

export interface PracticeAttemptHistory extends ListResult<PracticeAttempt> {
  best_score: number
}

export interface AnalyticsOverview {
  courses_in_plan: number
  completed_sessions: number
  study_minutes: number
  average_score: number
  completion_percent: number
}

export interface SkillProgress {
  skill: string
  progress_percent: number
  level: string
}

export type SkillProgressList = ItemCollection<SkillProgress>

export interface LearningStreak {
  current_days: number
  longest_days: number
  last_study_date: IsoDate | null
}

export interface WeakTopic {
  topic: string
  average_score: number
  attempts: number
  suggested_action: string
}

export type WeakTopicList = ItemCollection<WeakTopic>

export interface Recommendation {
  kind: string
  title: string
  reason: string
  action_id: EntityId | null
}

export type RecommendationList = ItemCollection<Recommendation>

export interface HealthStatus {
  status: string
}
