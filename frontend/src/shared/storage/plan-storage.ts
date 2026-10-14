import type { PlanStorage } from '@/shared/services/ports'
import type { UiPlan } from '@/shared/types/learning'

export const PLAN_STORAGE_KEY = 'localstudy.active-plan.v2'
const LEGACY_PLAN_STORAGE_KEY = 'localstudy.active-plan.v1'
type KeyValueStorage = Pick<Storage, 'getItem' | 'setItem' | 'removeItem'>

export class BrowserPlanStorage implements PlanStorage {
  constructor(private readonly getStorage: () => KeyValueStorage) {}

  read(): UiPlan | null {
    try {
      const storage = this.getStorage()
      storage.removeItem(LEGACY_PLAN_STORAGE_KEY)
      const raw = storage.getItem(PLAN_STORAGE_KEY)
      if (!raw) return null
      const snapshot = JSON.parse(raw) as { version?: unknown; plan?: Partial<UiPlan> } | null
      const plan = snapshot?.plan
      if (
        snapshot?.version !== 2 ||
        typeof plan?.id !== 'string' ||
        !plan.id ||
        typeof plan.title !== 'string' ||
        !plan.title ||
        typeof plan.courseId !== 'string' ||
        !plan.courseId ||
        typeof plan.weeklyMinutes !== 'number' ||
        !Number.isFinite(plan.weeklyMinutes) ||
        !Array.isArray(plan.milestones)
      ) {
        this.clear()
        return null
      }
      return plan as UiPlan
    } catch {
      this.clear()
      return null
    }
  }

  write(plan: UiPlan): boolean {
    try {
      const storage = this.getStorage()
      storage.setItem(PLAN_STORAGE_KEY, JSON.stringify({ version: 2, plan }))
      storage.removeItem(LEGACY_PLAN_STORAGE_KEY)
      return true
    } catch {
      return false
    }
  }

  clear(): void {
    try {
      const storage = this.getStorage()
      storage.removeItem(PLAN_STORAGE_KEY)
      storage.removeItem(LEGACY_PLAN_STORAGE_KEY)
    } catch {
      // Storage may be unavailable; clearing the in-memory plan still succeeds.
    }
  }
}
