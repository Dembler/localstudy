import { apiRequest, type ApiRequestOptions } from './client'
import type {
  CourseDetail,
  CourseList,
  CourseListParams,
  CourseSearchParams,
  EntityId,
  LessonPreview,
} from './types'

export async function listCourses(
  params: CourseListParams = {},
  options?: ApiRequestOptions,
): Promise<CourseList> {
  return apiRequest<CourseList>('/courses', { ...options, query: params })
}

export async function searchCourses(
  params: CourseSearchParams,
  options?: ApiRequestOptions,
): Promise<CourseList> {
  return apiRequest<CourseList>('/courses/search', { ...options, query: { q: params.query } })
}

export async function getCourse(
  courseId: EntityId,
  options?: ApiRequestOptions,
): Promise<CourseDetail> {
  return apiRequest<CourseDetail>(`/courses/${encodeURIComponent(courseId)}`, options)
}

export async function getCoursePrerequisites(
  courseId: EntityId,
  options?: ApiRequestOptions,
): Promise<CourseList> {
  return apiRequest<CourseList>(`/courses/${encodeURIComponent(courseId)}/prerequisites`, options)
}

export async function getLessonPreview(
  lessonId: EntityId,
  options?: ApiRequestOptions,
): Promise<LessonPreview> {
  return apiRequest<LessonPreview>(`/lessons/${encodeURIComponent(lessonId)}/preview`, options)
}

export const catalogApi = {
  listCourses,
  searchCourses,
  getCourse,
  getCoursePrerequisites,
  getLessonPreview,
} as const
