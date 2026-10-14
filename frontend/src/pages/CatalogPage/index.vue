<script setup lang="ts">
import { BookOpen, Check, Clock3 } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Progress } from '@/components/ui/progress'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
} from '@/components/ui/sheet'
import { Skeleton } from '@/components/ui/skeleton'
import { usePlanStore } from '@/shared/stores/plans'
import { useCatalogStore } from '@/shared/stores/catalog'
import { useNoticesStore } from '@/shared/stores/notices'

const plansStore = usePlanStore()
const { plan, goalLoading: catalogActionLoading } = storeToRefs(plansStore)
const catalogStore = useCatalogStore()
const {
  courses,
  selectedCourse,
  loading: catalogLoading,
  error: catalogError,
  demoMode: catalogDemoMode,
} = storeToRefs(catalogStore)
const noticesStore = useNoticesStore()
const { actionMessage } = storeToRefs(noticesStore)
const router = useRouter()

const query = ref('')
const category = ref('Все направления')
const level = ref('Любой уровень')
const detailOpen = ref(false)
const goalAdded = ref(false)

const categories = computed(() => [
  'Все направления',
  ...new Set(courses.value.map((item) => item.category)),
])

function pluralizeRu(value: number, one: string, few: string, many: string): string {
  const mod100 = value % 100
  const mod10 = value % 10
  if (mod100 >= 11 && mod100 <= 14) return many
  if (mod10 === 1) return one
  if (mod10 >= 2 && mod10 <= 4) return few
  return many
}

const formatHours = (value: number) => `${value} ${pluralizeRu(value, 'час', 'часа', 'часов')}`
const formatLessons = (value: number) => `${value} ${pluralizeRu(value, 'урок', 'урока', 'уроков')}`

const visibleCourses = computed(() => {
  const needle = query.value.trim().toLocaleLowerCase('ru')
  return courses.value.filter((course) => {
    const matchesText =
      !needle ||
      `${course.title} ${course.description} ${course.skills.join(' ')}`
        .toLocaleLowerCase('ru')
        .includes(needle)
    return (
      matchesText &&
      (category.value === 'Все направления' || course.category === category.value) &&
      (level.value === 'Любой уровень' || course.level === level.value)
    )
  })
})

const visibleSelectedCourse = computed(() =>
  visibleCourses.value.some((course) => course.id === selectedCourse.value?.id)
    ? selectedCourse.value
    : null,
)
const resultLabel = computed(() => {
  const value = visibleCourses.value.length
  return `${value} ${pluralizeRu(value, 'курс', 'курса', 'курсов')}`
})

const resetFilters = async () => {
  query.value = ''
  category.value = 'Все направления'
  level.value = 'Любой уровень'
  await catalogStore.loadCatalog()
}
const selectCourse = async (courseId: string) => {
  goalAdded.value = false
  await catalogStore.selectCourse(courseId)
  if (globalThis.matchMedia('(max-width: 760px)').matches) detailOpen.value = true
}
const addCourse = async () => {
  if (!selectedCourse.value) return
  if (!plan.value) {
    await router.push({ path: '/plan', query: { course: selectedCourse.value.id } })
    return
  }
  goalAdded.value = (await plansStore.addCourseGoal(selectedCourse.value)) === true
  if (goalAdded.value) detailOpen.value = false
}

const primaryLabel = computed(() => {
  if (!plan.value) return 'Выбрать для моей цели'
  if (goalAdded.value) return 'Цель сохранена'
  return 'Сделать курс новой целью'
})

const runPrimary = async () => {
  if (goalAdded.value) return
  await addCourse()
}

onMounted(() => {
  noticesStore.clearActionMessage()
  return Promise.all([plansStore.loadPlan(), catalogStore.loadCatalog()])
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header__copy">
        <span class="eyebrow">Развитие</span>
        <h1>Курсы</h1>
        <p>
          Сравните содержание и выберите курс для новой цели — без обещаний автоматического
          зачисления.
        </p>
      </div>
    </header>

    <Alert v-if="catalogDemoMode" class="mb-4 border-neutral-300">
      <AlertTitle>Показаны демонстрационные данные</AlertTitle>
      <AlertDescription>
        Каталог сейчас недоступен. Выбрать такой курс для реального плана нельзя.
      </AlertDescription>
    </Alert>
    <div class="mb-4 min-h-12">
      <Alert v-if="actionMessage" class="border-neutral-300" role="status">
        <AlertDescription>{{ actionMessage }}</AlertDescription>
      </Alert>
    </div>

    <Card class="mb-5">
      <CardContent class="catalog-filters" role="search">
        <div class="grid min-w-0 gap-2">
          <Label for="catalog-search">Поиск</Label>
          <Input
            id="catalog-search"
            v-model="query"
            type="search"
            placeholder="Курс, навык или тема"
          />
        </div>
        <div class="grid min-w-0 gap-2">
          <Label for="catalog-category">Направление</Label>
          <Select v-model="category">
            <SelectTrigger id="catalog-category" class="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem v-for="item in categories" :key="item" :value="item">
                {{ item }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="grid min-w-0 gap-2">
          <Label for="catalog-level">Уровень</Label>
          <Select v-model="level">
            <SelectTrigger id="catalog-level" class="w-full"><SelectValue /></SelectTrigger>
            <SelectContent>
              <SelectItem
                v-for="item in ['Любой уровень', 'Начальный', 'Средний', 'Продвинутый']"
                :key="item"
                :value="item"
              >
                {{ item }}
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
      </CardContent>
    </Card>

    <Card v-if="catalogLoading && !courses.length" class="min-h-72">
      <CardContent class="grid min-h-72 gap-3 p-6 sm:grid-cols-[minmax(0,1fr)_360px]">
        <div class="grid content-center gap-3">
          <Skeleton class="h-28 w-full" /><Skeleton class="h-28 w-full" />
        </div>
        <Skeleton class="h-full min-h-52 w-full" />
      </CardContent>
    </Card>
    <Alert v-else-if="catalogError && !courses.length" class="min-h-72 content-center">
      <AlertTitle>Не удалось открыть каталог</AlertTitle>
      <AlertDescription class="grid gap-4">
        <span>{{ catalogError }}</span
        ><Button variant="outline" class="w-fit" @click="catalogStore.loadCatalog">
          Повторить
        </Button>
      </AlertDescription>
    </Alert>
    <div v-else class="catalog-layout">
      <section class="course-list" aria-label="Результаты поиска">
        <div class="flex items-center justify-between gap-3 px-0.5 pb-1 text-xs">
          <strong>{{ resultLabel }}</strong>
          <span class="text-neutral-600">По названию, описанию и навыкам</span>
        </div>

        <Card v-if="!visibleCourses.length">
          <CardContent
            class="flex min-h-52 flex-col items-center justify-center gap-4 p-6 text-center"
          >
            <div>
              <h2 class="text-lg font-semibold">Ничего не найдено</h2>
              <p class="mt-2 text-sm text-neutral-600">
                Попробуйте другой запрос или сбросьте фильтры.
              </p>
            </div>
            <Button variant="outline" type="button" @click="resetFilters">Сбросить фильтры</Button>
          </CardContent>
        </Card>

        <Button
          v-for="course in visibleCourses"
          :key="course.id"
          variant="outline"
          class="course-row"
          :class="{ 'course-row--selected': selectedCourse?.id === course.id }"
          type="button"
          :aria-pressed="selectedCourse?.id === course.id"
          @click="selectCourse(course.id)"
        >
          <span class="flex min-w-0 flex-wrap items-center justify-between gap-2">
            <Badge variant="secondary" class="rounded-md">{{ course.level }}</Badge>
            <span class="text-xs text-neutral-600">{{ course.category }}</span>
          </span>
          <strong class="text-base leading-snug">{{ course.title }}</strong>
          <span class="text-sm leading-relaxed text-neutral-600">{{ course.description }}</span>
          <span class="flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-600">
            <span class="inline-flex items-center gap-1.5 whitespace-nowrap"
              ><Clock3 :size="14" />{{ course.durationHours }} ч</span
            >
            <span class="inline-flex items-center gap-1.5 whitespace-nowrap"
              ><BookOpen :size="14" />{{ formatLessons(course.lessonsCount) }}</span
            >
          </span>
          <span v-if="course.progress" class="grid gap-2">
            <span class="flex items-center justify-between text-xs"
              ><span>Уже изучено</span><strong>{{ course.progress }}%</strong></span
            >
            <Progress :model-value="course.progress" />
          </span>
        </Button>
      </section>

      <aside class="catalog-detail" aria-label="Карточка курса">
        <Card v-if="visibleSelectedCourse">
          <CardHeader><CardTitle>О курсе</CardTitle></CardHeader>
          <CardContent>
            <div class="flex flex-wrap items-center justify-between gap-2">
              <Badge variant="secondary" class="rounded-md">
                {{ visibleSelectedCourse.level }}
              </Badge>
              <span class="text-xs text-neutral-600">{{
                formatHours(visibleSelectedCourse.durationHours)
              }}</span>
            </div>
            <h2 class="mt-4 mb-2 text-xl leading-snug font-semibold tracking-tight">
              {{ visibleSelectedCourse.title }}
            </h2>
            <p class="m-0 text-sm leading-relaxed text-neutral-600">
              {{ visibleSelectedCourse.description }}
            </p>
            <Separator class="my-5" />
            <strong class="text-sm">Что освоите</strong>
            <ul class="mt-3 grid gap-3 p-0 text-sm">
              <li
                v-for="skill in visibleSelectedCourse.skills"
                :key="skill"
                class="flex items-start gap-2"
              >
                <Check class="mt-0.5 shrink-0" :size="16" /> <span>{{ skill }}</span>
              </li>
            </ul>
            <Button
              class="mt-6 w-full"
              type="button"
              :disabled="catalogActionLoading || catalogDemoMode || goalAdded"
              @click="runPrimary"
            >
              {{ catalogActionLoading ? 'Сохраняем…' : primaryLabel }}
            </Button>
            <p class="mt-3 mb-0 text-xs leading-relaxed text-neutral-600">
              {{
                !plan
                  ? 'Курс будет выбран для настройки вашего первого учебного плана.'
                  : goalAdded
                    ? 'Цель сохранена. Набор курсов текущего плана не изменился.'
                    : 'Создадим новую цель, но набор курсов текущего плана не изменится.'
              }}
            </p>
          </CardContent>
        </Card>
      </aside>
    </div>

    <Sheet v-model:open="detailOpen">
      <SheetContent side="bottom" class="max-h-[88vh] overflow-y-auto rounded-t-lg">
        <template v-if="selectedCourse">
          <SheetHeader class="text-left">
            <SheetTitle>{{ selectedCourse.title }}</SheetTitle>
            <SheetDescription>{{ selectedCourse.description }}</SheetDescription>
          </SheetHeader>
          <div class="mt-5 flex flex-wrap items-center gap-2">
            <Badge variant="secondary" class="rounded-md">{{ selectedCourse.level }}</Badge>
            <span class="text-xs text-neutral-600"
              >{{ formatHours(selectedCourse.durationHours) }} ·
              {{ formatLessons(selectedCourse.lessonsCount) }}</span
            >
          </div>
          <Separator class="my-5" />
          <strong class="text-sm">Что освоите</strong>
          <ul class="mt-3 grid gap-3 p-0 text-sm">
            <li v-for="skill in selectedCourse.skills" :key="skill" class="flex items-start gap-2">
              <Check class="mt-0.5 shrink-0" :size="16" /> <span>{{ skill }}</span>
            </li>
          </ul>
          <Button
            class="mt-6 w-full"
            type="button"
            :disabled="catalogActionLoading || catalogDemoMode || goalAdded"
            @click="runPrimary"
          >
            {{ catalogActionLoading ? 'Сохраняем…' : primaryLabel }}
          </Button>
        </template>
      </SheetContent>
    </Sheet>
  </div>
</template>

<style scoped>
.catalog-filters {
  display: grid;
  grid-template-columns: minmax(240px, 1fr) minmax(170px, 0.55fr) minmax(160px, 0.48fr);
  gap: 12px;
  align-items: end;
  padding: 16px;
}
.catalog-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(360px, 390px);
  gap: 20px;
  align-items: start;
}
.course-list {
  display: grid;
  min-width: 0;
  gap: 10px;
}
.course-row {
  display: grid;
  width: 100%;
  height: auto;
  min-width: 0;
  gap: 9px;
  padding: 16px;
  color: inherit;
  background: white;
  text-align: left;
  white-space: normal;
}
.course-row:hover {
  border-color: #a3a3a3;
}
.course-row--selected {
  border-color: #0a0a0a;
  outline: 1px solid #0a0a0a;
  outline-offset: -2px;
}
.catalog-detail {
  position: sticky;
  top: 24px;
  min-width: 0;
}
@media (max-width: 1023px) {
  .catalog-filters {
    grid-template-columns: minmax(240px, 1fr) repeat(2, minmax(150px, 0.5fr));
  }
  .catalog-layout {
    grid-template-columns: minmax(0, 1fr) minmax(320px, 360px);
  }
}
@media (max-width: 959px) {
  .catalog-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .catalog-detail {
    position: static;
  }
}
@media (max-width: 767px) {
  .catalog-filters {
    grid-template-columns: minmax(0, 1fr);
  }
  .catalog-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .catalog-detail {
    display: none;
  }
}
</style>
