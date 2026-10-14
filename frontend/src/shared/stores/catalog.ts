import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import { errorMessage } from '@/shared/presentation/errors'
import { CATALOG_GATEWAY, useDependency } from '@/shared/services/ports'
import { demoCourses } from '@/shared/data/demo'
import { normalizeCourse } from '@/shared/presentation/catalog'
import type { UiCourse } from '@/shared/types/learning'

export const useCatalogStore = defineStore('catalog', () => {
  const catalogApi = useDependency(CATALOG_GATEWAY)
  const courses = ref<UiCourse[]>([])
  const selectedCourseId = ref<string | null>(null)
  const loading = ref(false)
  const error = ref('')
  const demoMode = ref(false)
  const selectedCourse = computed(
    () =>
      courses.value.find((item) => item.id === selectedCourseId.value) ?? courses.value[0] ?? null,
  )

  async function loadCatalog() {
    loading.value = true
    error.value = ''
    try {
      const result = await catalogApi.listCourses()
      courses.value = result.items.map(normalizeCourse)
      selectedCourseId.value = courses.value[0]?.id ?? null
      demoMode.value = false
    } catch (cause) {
      error.value = errorMessage(cause)
      demoMode.value = true
      courses.value = structuredClone(demoCourses)
      selectedCourseId.value = courses.value[0]?.id ?? null
    } finally {
      loading.value = false
    }
  }

  async function searchCatalog(query: string) {
    if (!query.trim() || demoMode.value) return
    loading.value = true
    try {
      const result = await catalogApi.searchCourses({ query })
      courses.value = result.items.map(normalizeCourse)
      selectedCourseId.value = courses.value[0]?.id ?? null
    } catch (cause) {
      error.value = errorMessage(cause)
    } finally {
      loading.value = false
    }
  }

  async function selectCourse(courseId: string) {
    selectedCourseId.value = courseId
    if (demoMode.value) return
    try {
      const detail = await catalogApi.getCourse(courseId)
      const normalized = normalizeCourse(detail)
      normalized.skills = detail.skills
      courses.value = courses.value.map((item) => (item.id === courseId ? normalized : item))
    } catch (cause) {
      error.value = errorMessage(cause)
    }
  }

  return {
    courses,
    selectedCourse,
    loading,
    error,
    demoMode,
    loadCatalog,
    searchCatalog,
    selectCourse,
  }
})
