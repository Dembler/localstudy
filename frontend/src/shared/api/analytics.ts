import { apiRequest, type ApiRequestOptions } from './client'
import type {
  AnalyticsOverview,
  LearningStreak,
  RecommendationList,
  SkillProgressList,
  WeakTopicList,
} from './types'

export async function getOverview(options?: ApiRequestOptions): Promise<AnalyticsOverview> {
  return apiRequest<AnalyticsOverview>('/analytics/overview', options)
}

export async function getSkills(options?: ApiRequestOptions): Promise<SkillProgressList> {
  return apiRequest<SkillProgressList>('/analytics/skills', options)
}

export async function getStreak(options?: ApiRequestOptions): Promise<LearningStreak> {
  return apiRequest<LearningStreak>('/analytics/streak', options)
}

export async function getWeakTopics(options?: ApiRequestOptions): Promise<WeakTopicList> {
  return apiRequest<WeakTopicList>('/analytics/weak-topics', options)
}

export async function getRecommendations(options?: ApiRequestOptions): Promise<RecommendationList> {
  return apiRequest<RecommendationList>('/analytics/recommendations', options)
}

export const analyticsApi = {
  getOverview,
  getSkills,
  getStreak,
  getWeakTopics,
  getRecommendations,
} as const
