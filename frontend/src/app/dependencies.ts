import type { App } from 'vue'

import { analyticsApi, catalogApi, plansApi, practiceApi, sessionsApi } from '@/shared/api'
import {
  ANALYTICS_GATEWAY,
  CATALOG_GATEWAY,
  PLANS_GATEWAY,
  PRACTICE_GATEWAY,
  SESSIONS_GATEWAY,
  PLAN_STORAGE,
} from '@/shared/services/ports'
import { BrowserPlanStorage } from '@/shared/storage/plan-storage'

export function provideDependencies(app: App): void {
  app.provide(CATALOG_GATEWAY, catalogApi)
  app.provide(PLANS_GATEWAY, plansApi)
  app.provide(SESSIONS_GATEWAY, sessionsApi)
  app.provide(PRACTICE_GATEWAY, practiceApi)
  app.provide(ANALYTICS_GATEWAY, analyticsApi)
  app.provide(PLAN_STORAGE, new BrowserPlanStorage(() => window.localStorage))
}
