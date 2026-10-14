import { apiRequest, type ApiRequestOptions } from './client'
import type {
  EntityId,
  NextAssignmentParams,
  PracticeAssignment,
  PracticeAttempt,
  PracticeAttemptHistory,
  PracticeHint,
  PracticeRetry,
  SubmitAttemptInput,
} from './types'

export async function getNextAssignment(
  params: NextAssignmentParams,
  options?: ApiRequestOptions,
): Promise<PracticeAssignment> {
  return apiRequest<PracticeAssignment>('/practice/next', { ...options, query: params })
}

export async function submitAttempt(
  assignmentId: EntityId,
  input: SubmitAttemptInput,
  options?: ApiRequestOptions,
): Promise<PracticeAttempt> {
  return apiRequest<PracticeAttempt>(
    `/practice/assignments/${encodeURIComponent(assignmentId)}/attempts`,
    { ...options, method: 'POST', body: input },
  )
}

export async function requestHint(
  assignmentId: EntityId,
  options?: ApiRequestOptions,
): Promise<PracticeHint> {
  return apiRequest<PracticeHint>(
    `/practice/assignments/${encodeURIComponent(assignmentId)}/hint`,
    { ...options, method: 'POST' },
  )
}

export async function retryAssignment(
  assignmentId: EntityId,
  options?: ApiRequestOptions,
): Promise<PracticeRetry> {
  return apiRequest<PracticeRetry>(
    `/practice/assignments/${encodeURIComponent(assignmentId)}/retry`,
    { ...options, method: 'POST' },
  )
}

export async function listAttempts(
  assignmentId: EntityId,
  options?: ApiRequestOptions,
): Promise<PracticeAttemptHistory> {
  return apiRequest<PracticeAttemptHistory>(
    `/practice/assignments/${encodeURIComponent(assignmentId)}/attempts`,
    options,
  )
}

export const practiceApi = {
  getNextAssignment,
  submitAttempt,
  requestHint,
  retryAssignment,
  listAttempts,
} as const
