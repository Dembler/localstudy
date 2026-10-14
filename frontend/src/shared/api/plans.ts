import { apiRequest, type ApiRequestOptions } from './client'
import type {
  AddPlanGoalInput,
  CreatePlanInput,
  EntityId,
  PlanForecast,
  PlanGoal,
  RebalanceResult,
  StudyPlan,
  UpdateWorkloadInput,
} from './types'

export async function createPlan(
  input: CreatePlanInput,
  options?: ApiRequestOptions,
): Promise<StudyPlan> {
  return apiRequest<StudyPlan>('/plans', { ...options, method: 'POST', body: input })
}

export async function updatePlanWorkload(
  planId: EntityId,
  input: UpdateWorkloadInput,
  options?: ApiRequestOptions,
): Promise<StudyPlan> {
  return apiRequest<StudyPlan>(`/plans/${encodeURIComponent(planId)}/workload`, {
    ...options,
    method: 'PATCH',
    body: input,
  })
}

export async function addPlanGoal(
  planId: EntityId,
  input: AddPlanGoalInput,
  options?: ApiRequestOptions,
): Promise<PlanGoal> {
  return apiRequest<PlanGoal>(`/plans/${encodeURIComponent(planId)}/goals`, {
    ...options,
    method: 'POST',
    body: input,
  })
}

export async function rebalancePlan(
  planId: EntityId,
  options?: ApiRequestOptions,
): Promise<RebalanceResult> {
  return apiRequest<RebalanceResult>(`/plans/${encodeURIComponent(planId)}/rebalance`, {
    ...options,
    method: 'POST',
  })
}

export async function getPlanForecast(
  planId: EntityId,
  options?: ApiRequestOptions,
): Promise<PlanForecast> {
  return apiRequest<PlanForecast>(`/plans/${encodeURIComponent(planId)}/forecast`, options)
}

export async function deletePlan(planId: EntityId, options?: ApiRequestOptions): Promise<void> {
  return apiRequest<void>(`/plans/${encodeURIComponent(planId)}`, {
    ...options,
    method: 'DELETE',
  })
}

export async function deletePlanGoal(
  planId: EntityId,
  goalId: EntityId,
  options?: ApiRequestOptions,
): Promise<void> {
  return apiRequest<void>(
    `/plans/${encodeURIComponent(planId)}/goals/${encodeURIComponent(goalId)}`,
    { ...options, method: 'DELETE' },
  )
}

export async function removePlanCourse(
  planId: EntityId,
  courseId: EntityId,
  options?: ApiRequestOptions,
): Promise<void> {
  return apiRequest<void>(
    `/plans/${encodeURIComponent(planId)}/courses/${encodeURIComponent(courseId)}`,
    { ...options, method: 'DELETE' },
  )
}

export const plansApi = {
  createPlan,
  updatePlanWorkload,
  addPlanGoal,
  rebalancePlan,
  getPlanForecast,
  deletePlan,
  deletePlanGoal,
  removePlanCourse,
} as const
