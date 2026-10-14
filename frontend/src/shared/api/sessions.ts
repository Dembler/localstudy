import { apiRequest, type ApiRequestOptions } from './client'
import type {
  CompleteSessionInput,
  EntityId,
  RescheduleSessionInput,
  ScheduleSessionInput,
  SessionCalendar,
  SessionCalendarParams,
  StudySession,
} from './types'

export async function getSessionCalendar(
  params: SessionCalendarParams = {},
  options?: ApiRequestOptions,
): Promise<SessionCalendar> {
  return apiRequest<SessionCalendar>('/sessions/calendar', { ...options, query: params })
}

export async function scheduleSession(
  input: ScheduleSessionInput,
  options?: ApiRequestOptions,
): Promise<StudySession> {
  return apiRequest<StudySession>('/sessions', { ...options, method: 'POST', body: input })
}

export async function startSession(
  sessionId: EntityId,
  options?: ApiRequestOptions,
): Promise<StudySession> {
  return apiRequest<StudySession>(`/sessions/${encodeURIComponent(sessionId)}/start`, {
    ...options,
    method: 'POST',
  })
}

export async function completeSession(
  sessionId: EntityId,
  input: CompleteSessionInput,
  options?: ApiRequestOptions,
): Promise<StudySession> {
  return apiRequest<StudySession>(`/sessions/${encodeURIComponent(sessionId)}/complete`, {
    ...options,
    method: 'POST',
    body: input,
  })
}

export async function rescheduleSession(
  sessionId: EntityId,
  input: RescheduleSessionInput,
  options?: ApiRequestOptions,
): Promise<StudySession> {
  return apiRequest<StudySession>(`/sessions/${encodeURIComponent(sessionId)}/reschedule`, {
    ...options,
    method: 'POST',
    body: input,
  })
}

export const sessionsApi = {
  getSessionCalendar,
  scheduleSession,
  startSession,
  completeSession,
  rescheduleSession,
} as const
