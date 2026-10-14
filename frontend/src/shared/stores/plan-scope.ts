import { watch } from 'vue'

export function usePlanScope(planId: () => string | undefined, reset: () => void) {
  let generation = 0
  watch(
    planId,
    () => {
      generation += 1
      reset()
    },
    { flush: 'sync' },
  )

  return function captureScope() {
    const currentGeneration = generation
    return () => generation === currentGeneration
  }
}
