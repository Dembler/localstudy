<script setup lang="ts">
import {
  ArrowRight,
  BookOpen,
  CalendarCheck2,
  CalendarClock,
  Check,
  ChevronDown,
  Flag,
  Play,
  RefreshCw,
  Settings2,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref, watch } from 'vue'
import { RouterLink, useRoute, useRouter } from 'vue-router'

import { Alert, AlertDescription } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { usePlanStore } from '@/shared/stores/plans'
import { useCatalogStore } from '@/shared/stores/catalog'
import { useSessionsStore } from '@/shared/stores/sessions'
import { usePracticeStore } from '@/shared/stores/practice'
import { useNoticesStore } from '@/shared/stores/notices'

const plansStore = usePlanStore()
const {
  plan,
  actionLoading: planActionLoading,
  loading: planLoading,
  error: planError,
} = storeToRefs(plansStore)
const catalogStore = useCatalogStore()
const { courses, demoMode: catalogDemoMode } = storeToRefs(catalogStore)
const sessionsStore = useSessionsStore()
const { sessions, actionLoading: sessionActionLoading } = storeToRefs(sessionsStore)
const practiceStore = usePracticeStore()
const { assignment } = storeToRefs(practiceStore)
const noticesStore = useNoticesStore()
const { actionMessage } = storeToRefs(noticesStore)
const route = useRoute()
const router = useRouter()

const weeklyHours = ref(4)
const setupCourseId = ref('')
const settingsOpen = ref(false)
const resetDialogOpen = ref(false)

const weeklyLabel = computed(() => {
  const minutes = plan.value?.weeklyMinutes ?? weeklyHours.value * 60
  return `${Math.floor(minutes / 60)} ч${minutes % 60 ? ` ${minutes % 60} мин` : ''}`
})

const unfinishedSessions = computed(() =>
  [...sessions.value]
    .filter((item) => item.status === 'scheduled' || item.status === 'in_progress')
    .sort((a, b) => {
      if (a.status === 'in_progress' && b.status !== 'in_progress') return -1
      if (b.status === 'in_progress' && a.status !== 'in_progress') return 1
      return Date.parse(a.startsAt) - Date.parse(b.startsAt)
    }),
)
const focusSession = computed(() => unfinishedSessions.value[0] ?? null)
const nextSession = computed(() => unfinishedSessions.value[1] ?? null)
const canPractice = computed(
  () => Boolean(assignment.value) && sessions.value.some((item) => item.status === 'completed'),
)
const practiceIsNext = computed(
  () => canPractice.value && focusSession.value?.status !== 'in_progress',
)

const primaryLabel = computed(() => {
  if (focusSession.value?.status === 'in_progress') return 'Завершить занятие'
  if (practiceIsNext.value) return 'Перейти к практике'
  if (focusSession.value) return 'Начать занятие'
  if (canPractice.value) return 'Перейти к практике'
  return 'Запланировать занятие'
})

const formatDateTime = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))

const submitCreate = async () => {
  const course = courses.value.find((item) => item.id === setupCourseId.value)
  if (!course) return
  await plansStore.createNewPlan({
    weeklyMinutes: weeklyHours.value * 60,
    course,
  })
  if (plan.value) await Promise.all([sessionsStore.loadSessions(), practiceStore.loadPractice()])
}

const runPrimary = async () => {
  if (focusSession.value?.status === 'in_progress') {
    await sessionsStore.advanceSession(focusSession.value.id)
    return
  }
  if (practiceIsNext.value) {
    await router.push('/practice')
    return
  }
  if (focusSession.value) {
    await sessionsStore.advanceSession(focusSession.value.id)
    return
  }
  await router.push('/sessions')
}

const rebalanceSchedule = async () => {
  if (await plansStore.rebalanceCurrentPlan()) await sessionsStore.loadSessions()
}

const resetPlan = () => {
  plansStore.clearActivePlan()
  resetDialogOpen.value = false
}

watch(
  () => plan.value?.weeklyMinutes,
  (minutes) => {
    if (minutes) weeklyHours.value = Math.max(1, Math.round(minutes / 60))
  },
  { immediate: true },
)

onMounted(async () => {
  noticesStore.clearActionMessage()
  await Promise.all([plansStore.loadPlan(), catalogStore.loadCatalog()])
  const courseFromQuery = typeof route.query.course === 'string' ? route.query.course : ''
  setupCourseId.value = courses.value.find((course) => course.id === courseFromQuery)?.id ?? ''
  if (plan.value) await Promise.all([sessionsStore.loadSessions(), practiceStore.loadPractice()])
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header__copy">
        <span class="eyebrow">Ваше обучение</span>
        <h1>{{ plan ? 'Сегодня' : 'Начните обучение' }}</h1>
        <p>
          {{
            plan
              ? 'Сосредоточьтесь на одном ближайшем шаге — остальное подождёт.'
              : 'Выберите курс и удобный темп — остальное выстроим по шагам.'
          }}
        </p>
      </div>
    </header>

    <Card v-if="plan" class="mb-4">
      <CardContent class="grid grid-cols-2 gap-2 p-2 sm:grid-cols-4">
        <Button as-child size="sm"><RouterLink to="/plan">План</RouterLink></Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/sessions">Занятия</RouterLink>
        </Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/practice">Практика</RouterLink>
        </Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/analytics">Прогресс</RouterLink>
        </Button>
      </CardContent>
    </Card>

    <Card v-if="planLoading" class="min-h-52">
      <CardContent class="flex min-h-52 flex-col justify-center gap-4 p-6">
        <span class="text-sm font-medium">Открываем ваш план…</span>
        <Skeleton class="h-5 w-2/3" />
        <Skeleton class="h-20 w-full" />
        <Skeleton class="h-10 w-40" />
      </CardContent>
    </Card>

    <section v-else-if="!plan" class="onboarding" aria-labelledby="onboarding-title">
      <Card class="border-neutral-950 bg-neutral-950 text-white">
        <CardHeader class="gap-3">
          <Badge variant="secondary" class="w-fit rounded-md">Понятный старт</Badge>
          <CardTitle id="onboarding-title" class="text-2xl leading-tight sm:text-3xl">
            Начните с одного курса. Ритм построим вместе.
          </CardTitle>
          <CardDescription class="text-neutral-300">
            Выберите направление и время на неделю — первое занятие появится в вашем плане.
          </CardDescription>
        </CardHeader>
        <CardContent class="grid gap-2 sm:grid-cols-3">
          <Badge variant="secondary" class="h-10 justify-center rounded-md">
            <BookOpen /> Курс
          </Badge>
          <Badge variant="secondary" class="h-10 justify-center rounded-md">
            <CalendarCheck2 /> Ритм
          </Badge>
          <Badge variant="secondary" class="h-10 justify-center rounded-md">
            <Flag /> Первое занятие
          </Badge>
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <CardDescription>Настройка маршрута</CardDescription>
          <CardTitle>Выберите курс и темп</CardTitle>
          <CardDescription>
            Этого достаточно, чтобы начать. Параметры можно изменить позже.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <form class="onboarding__form" @submit.prevent="submitCreate">
            <div class="onboarding__fields">
              <div class="grid min-w-0 gap-2">
                <Label for="setup-course">Что хотите изучать?</Label>
                <Select v-model="setupCourseId">
                  <SelectTrigger id="setup-course" class="w-full bg-white">
                    <SelectValue placeholder="Выберите курс" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="course in courses" :key="course.id" :value="course.id">
                      {{ course.title }}
                    </SelectItem>
                  </SelectContent>
                </Select>
                <span class="text-xs text-neutral-600">
                  Обязательные основы добавим в маршрут, а первое занятие возьмём из выбранного
                  курса.
                </span>
              </div>

              <div class="grid min-w-0 gap-2">
                <Label for="weekly-hours">Часов в неделю</Label>
                <Input
                  id="weekly-hours"
                  v-model.number="weeklyHours"
                  class="bg-white"
                  type="number"
                  min="1"
                  max="20"
                  required
                />
                <span class="text-xs text-neutral-600"
                  >Для старта обычно достаточно 3–5 часов.</span
                >
              </div>
            </div>

            <div class="grid min-h-12 gap-2">
              <Alert v-if="planError" class="border-neutral-400 bg-white" role="alert">
                <AlertDescription>
                  План не удалось создать. Проверьте подключение и попробуйте ещё раз.
                </AlertDescription>
              </Alert>
              <Alert v-if="catalogDemoMode" class="border-neutral-400 bg-white" role="alert">
                <AlertDescription>
                  Не удалось загрузить доступные курсы. Обновите список, чтобы создать настоящий
                  план.
                  <Button
                    variant="outline"
                    size="sm"
                    class="mt-3"
                    type="button"
                    @click="catalogStore.loadCatalog"
                  >
                    Обновить курсы
                  </Button>
                </AlertDescription>
              </Alert>
            </div>

            <div class="onboarding__submit">
              <Button
                type="submit"
                size="lg"
                :disabled="planActionLoading || catalogDemoMode || !setupCourseId"
              >
                <Flag /> {{ planActionLoading ? 'Создаём маршрут…' : 'Создать маршрут' }}
              </Button>
              <span>После этого предложим запланировать первое занятие.</span>
            </div>
          </form>
        </CardContent>
      </Card>
    </section>

    <template v-else>
      <div class="mb-4 min-h-12">
        <Alert v-if="actionMessage || planError" class="border-neutral-300" role="status">
          <AlertDescription>{{ planError || actionMessage }}</AlertDescription>
        </Alert>
      </div>

      <Card class="mb-4" aria-labelledby="today-focus-title">
        <CardContent class="today-focus">
          <div class="today-focus__copy">
            <span class="eyebrow">Главное сейчас</span>
            <template v-if="practiceIsNext && assignment">
              <Badge variant="secondary" class="rounded-md">После занятия</Badge>
              <h2 id="today-focus-title" class="mt-3">Закрепите тему практикой</h2>
              <p>{{ assignment.title }} · около {{ assignment.estimatedMinutes }} минут</p>
            </template>
            <template v-else-if="focusSession">
              <div class="mb-3 flex flex-wrap items-center gap-2">
                <Badge variant="secondary" class="rounded-md">
                  {{ focusSession.status === 'in_progress' ? 'Идёт сейчас' : 'Ближайшее занятие' }}
                </Badge>
                <span class="text-xs text-neutral-600">
                  {{ formatDateTime(focusSession.startsAt) }} ·
                  {{ focusSession.durationMinutes }} мин
                </span>
              </div>
              <h2 id="today-focus-title">{{ focusSession.title }}</h2>
              <p>{{ focusSession.courseTitle }}</p>
            </template>
            <template v-else-if="canPractice && assignment">
              <Badge variant="secondary" class="rounded-md">Практика доступна</Badge>
              <h2 id="today-focus-title" class="mt-3">Закрепите тему практикой</h2>
              <p>{{ assignment.title }} · около {{ assignment.estimatedMinutes }} минут</p>
            </template>
            <template v-else>
              <Badge variant="secondary" class="rounded-md">План готов</Badge>
              <h2 id="today-focus-title" class="mt-3">Добавьте первое занятие</h2>
              <p>Выберите удобное время — начнём с первого шага вашего учебного маршрута.</p>
            </template>
          </div>
          <Button size="lg" type="button" :disabled="sessionActionLoading" @click="runPrimary">
            <Check v-if="focusSession?.status === 'in_progress' && !practiceIsNext" />
            <Play v-else-if="focusSession && !practiceIsNext" />
            <ArrowRight v-else />
            {{ sessionActionLoading ? 'Сохраняем…' : primaryLabel }}
          </Button>
        </CardContent>
      </Card>

      <div class="today-layout">
        <Card>
          <CardHeader>
            <CardTitle>Следующие шаги</CardTitle>
            <CardDescription>
              Показываем только ближайшее, чтобы не перегружать день.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <ol class="next-steps">
              <li v-if="practiceIsNext && assignment">
                <Badge variant="outline" class="rounded-md">Шаг 1</Badge>
                <div class="min-w-0">
                  <strong>Закрепить тему практикой</strong>
                  <span>{{ assignment.title }}</span>
                </div>
                <Badge variant="secondary" class="rounded-md">Сейчас</Badge>
              </li>
              <li v-if="focusSession">
                <Badge variant="outline" class="rounded-md">Шаг {{ practiceIsNext ? 2 : 1 }}</Badge>
                <div class="min-w-0">
                  <strong>{{ focusSession.title }}</strong>
                  <span>{{ formatDateTime(focusSession.startsAt) }}</span>
                </div>
                <Badge variant="secondary" class="rounded-md">
                  {{ focusSession.status === 'in_progress' ? 'Сейчас' : 'Позже' }}
                </Badge>
              </li>
              <li v-if="nextSession && !practiceIsNext">
                <Badge variant="outline" class="rounded-md">Шаг 2</Badge>
                <div class="min-w-0">
                  <strong>{{ nextSession.title }}</strong>
                  <span>{{ formatDateTime(nextSession.startsAt) }}</span>
                </div>
                <Badge variant="secondary" class="rounded-md">Позже</Badge>
              </li>
              <li v-if="!focusSession">
                <Badge variant="outline" class="rounded-md">Шаг 1</Badge>
                <div class="min-w-0">
                  <strong>{{
                    canPractice ? 'Выполнить практику' : 'Запланировать занятие'
                  }}</strong>
                  <span>{{
                    canPractice && assignment ? assignment.title : 'Выберите удобные дату и время'
                  }}</span>
                </div>
              </li>
            </ol>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Ваш маршрут</CardTitle></CardHeader>
          <CardContent>
            <div class="flex items-start gap-3">
              <BookOpen class="mt-0.5 shrink-0" :size="19" />
              <div class="min-w-0">
                <strong class="block text-sm leading-snug">{{ plan.title }}</strong>
                <span class="mt-1 block text-xs text-neutral-600">{{ weeklyLabel }} в неделю</span>
              </div>
            </div>
            <Separator class="my-4" />
            <div class="grid grid-cols-2 gap-3 text-xs">
              <div>
                <span class="text-neutral-600">Прогноз</span>
                <strong class="mt-1 block">{{ plan.forecastDate }}</strong>
              </div>
              <div>
                <span class="text-neutral-600">Занятий впереди</span>
                <strong class="mt-1 block">{{ unfinishedSessions.length }}</strong>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <Collapsible v-model:open="settingsOpen" class="plan-settings">
        <CollapsibleTrigger as-child>
          <Button variant="outline" class="w-full justify-between" type="button">
            <span class="inline-flex items-center gap-2"><Settings2 /> Настройки плана</span>
            <ChevronDown :class="{ 'rotate-180': settingsOpen }" />
          </Button>
        </CollapsibleTrigger>
        <CollapsibleContent>
          <div class="plan-settings__content">
            <div class="grid gap-2">
              <Label for="workload">Часов в неделю</Label>
              <div class="flex gap-2">
                <Input id="workload" v-model.number="weeklyHours" type="number" min="1" max="20" />
                <Button
                  variant="outline"
                  type="button"
                  :disabled="planActionLoading"
                  @click="plansStore.updateWorkload(weeklyHours * 60)"
                >
                  Сохранить
                </Button>
              </div>
            </div>
            <div class="plan-settings__meta">
              <CalendarClock :size="18" />
              <span>Прогноз завершения</span>
              <strong>{{ plan.forecastDate }}</strong>
            </div>
            <Button
              variant="outline"
              type="button"
              :disabled="planActionLoading"
              @click="rebalanceSchedule"
            >
              <RefreshCw :class="{ 'is-spinning': planActionLoading }" /> Перестроить расписание
            </Button>
            <Button variant="ghost" type="button" @click="resetDialogOpen = true">
              Выбрать другой курс
            </Button>
          </div>
        </CollapsibleContent>
      </Collapsible>

      <Dialog v-model:open="resetDialogOpen">
        <DialogContent class="sm:max-w-md">
          <DialogHeader>
            <DialogTitle>Выбрать другой курс?</DialogTitle>
            <DialogDescription>
              Текущий план исчезнет из этого браузера. Вернуться к нему через интерфейс пока не
              получится.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <Button variant="outline" type="button" @click="resetDialogOpen = false">
              Отмена
            </Button>
            <Button type="button" @click="resetPlan">Выбрать другой курс</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </template>
  </div>
</template>

<style scoped>
.onboarding {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 16px;
  align-items: stretch;
}
.onboarding__form {
  display: grid;
  min-width: 0;
  gap: 20px;
}
.onboarding__fields {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(150px, 0.45fr);
  gap: 16px;
}
.onboarding__submit {
  display: flex;
  align-items: center;
  gap: 14px;
}
.onboarding__submit > span {
  max-width: 220px;
  color: #525252;
  font-size: 11px;
  line-height: 1.45;
}
.today-focus {
  display: flex;
  gap: 24px;
  align-items: center;
  justify-content: space-between;
  padding: clamp(22px, 4vw, 36px);
}
.today-focus h2 {
  margin: 0;
  font-size: clamp(21px, 3vw, 30px);
  line-height: 1.2;
  letter-spacing: -0.035em;
}
.today-focus p {
  margin: 8px 0 0;
  color: #525252;
  font-size: 14px;
}
.today-layout {
  display: grid;
  grid-template-columns: minmax(0, 1.4fr) minmax(280px, 0.6fr);
  gap: 16px;
  align-items: start;
}
.next-steps {
  display: grid;
  gap: 0;
  margin: 0;
  padding: 0;
  list-style: none;
}
.next-steps li {
  display: grid;
  grid-template-columns: 64px minmax(0, 1fr) minmax(72px, auto);
  gap: 12px;
  align-items: center;
  min-height: 60px;
  padding: 8px 0;
}
.next-steps strong,
.next-steps span {
  display: block;
}
.next-steps strong {
  font-size: 13px;
  line-height: 1.4;
}
.next-steps div > span {
  margin-top: 3px;
  color: #525252;
  font-size: 11px;
}
.plan-settings {
  margin-top: 16px;
}
.plan-settings__content {
  display: grid;
  grid-template-columns: minmax(230px, 1fr) minmax(170px, 0.6fr) auto auto;
  gap: 16px;
  align-items: end;
  margin-top: 8px;
  padding: 18px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
  background: #fafafa;
}
.plan-settings__meta {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr);
  gap: 2px 8px;
  align-items: center;
  font-size: 12px;
}
.plan-settings__meta svg {
  grid-row: 1 / 3;
}
.plan-settings__meta span {
  color: #525252;
}
@media (max-width: 959px) {
  .onboarding {
    grid-template-columns: minmax(0, 1fr);
  }
  .today-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .plan-settings__content {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
}
@media (max-width: 767px) {
  .onboarding__fields,
  .plan-settings__content {
    grid-template-columns: minmax(0, 1fr);
  }
  .today-focus {
    align-items: stretch;
    flex-direction: column;
    gap: 16px;
  }
  .onboarding__submit {
    display: grid;
  }
  .onboarding__submit > *,
  .today-focus > [data-slot='button'] {
    width: 100%;
  }
  .next-steps li {
    grid-template-columns: minmax(0, 1fr);
    align-items: start;
  }
}
</style>
