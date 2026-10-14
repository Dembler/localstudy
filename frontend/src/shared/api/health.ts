import { rootRequest, type ApiRequestOptions } from './client'
import type { HealthStatus } from './types'

export async function getHealth(options?: ApiRequestOptions): Promise<HealthStatus> {
  return rootRequest<HealthStatus>('/health', options)
}

export const healthApi = { getHealth } as const
