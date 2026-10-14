<script setup lang="ts">
import { CalendarPlus, Check, ChevronDown, Clock3, History, Play, RotateCcw } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
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
import { Skeleton } from '@/components/ui/skeleton'
import type { UiSession } from '@/shared/types/learning'
import { usePlanStore } from '@/shared/stores/plans'
import { useSessionsStore } from '@/shared/stores/sessions'
import { useNoticesStore } from '@/shared/stores/notices'

const plansStore = usePlanStore()
const { plan, loading: planLoading } = storeToRefs(plansStore)
const sessionsStore = useSessionsStore()
const {
  sessions,
  selectedSessionId,
  loading: sessionsLoading,
  actionLoading: sessionActionLoading,
  error: sessionsError,
} = storeToRefs(sessionsStore)
const noticesStore = useNoticesStore()
const { actionMessage } = storeToRefs(noticesStore)

const showSchedule = ref(false)
const showCompleted = ref(false)
const scheduledAt = ref('')

const selectedSession = computed(
  () => sessions.value.find((item) => item.id === selectedSessionId.value) ?? null,
)
const unfinishedSessions = computed(() =>
  sessions.value.filter((item) => item.status === 'scheduled' || item.status === 'in_progress'),
)
const completedSessions = computed(() =>
  sessions.value.filter((item) => item.status === 'completed'),
)

const isToday = (value: string) => {
  const date = new Date(value)
  const now = new Date()
  return (
    date.getFullYear() === now.getFullYear() &&
    date.getMonth() === now.getMonth() &&
    date.getDate() === now.getDate()
  )
}

const isPast = (value: string) => Date.parse(value) < Date.now()

const sessionGroups = computed(() => {
  const today: UiSession[] = []
  const later: UiSession[] = []
  for (const session of unfinishedSessions.value) {
    if (isToday(session.startsAt)) today.push(session)
    else later.push(session)
  }
  return [
    { title: 'Сегодня', items: today },
    { title: 'Другие даты', items: later },
  ].filter((group) => group.items.length)
})

const primaryLabel = computed(() =>
  selectedSession.value?.status === 'in_progress' ? 'Завершить занятие' : 'Начать занятие',
)

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', {
    weekday: 'short',
    day: 'numeric',
    month: 'short',
  }).format(new Date(value))

const formatTime = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' }).format(new Date(value))

const runPrimary = async () => {
  if (!selectedSession.value) return
  await sessionsStore.advanceSession(selectedSession.value.id)
}

const schedule = async () => {
  const before = sessions.value.length
  await sessionsStore.scheduleLearningSession(scheduledAt.value)
  if (sessions.value.length > before) {
    showSchedule.value = false
    scheduledAt.value = ''
  }
}

onMounted(async () => {
  noticesStore.clearActionMessage()
  await plansStore.loadPlan()
  if (plan.value) await sessionsStore.loadSessions()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header__copy">
        <span class="eyebrow">Учебная неделя</span>
        <h1>Расписание</h1>
        <p>Выберите занятие, затем начните или завершите его одним понятным действием.</p>
      </div>
    </header>

    <Card class="mb-4">
      <CardContent class="grid grid-cols-2 gap-2 p-2 sm:grid-cols-4">
        <Button as-child size="sm" variant="ghost"><RouterLink to="/plan">План</RouterLink></Button>
        <Button as-child size="sm"><RouterLink to="/sessions">Занятия</RouterLink></Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/practice">Практика</RouterLink>
        </Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/analytics">Прогресс</RouterLink>
        </Button>
      </CardContent>
    </Card>

    <Card v-if="planLoading || (plan && sessionsLoading)" class="min-h-64">
      <CardContent class="grid min-h-64 gap-3 p-6 sm:grid-cols-[minmax(0,1fr)_320px]">
        <div class="grid content-center gap-3">
          <Skeleton class="h-16 w-full" /><Skeleton class="h-16 w-full" />
        </div>
        <Skeleton class="h-full min-h-40 w-full" />
      </CardContent>
    </Card>

    <Card v-else-if="!plan">
      <CardContent class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center">
        <div>
          <h2 class="text-lg font-semibold">Сначала настройте обучение</h2>
          <p class="mt-2 max-w-lg text-sm text-neutral-600">
            Расписание строится вокруг выбранного курса. Это займёт около минуты.
          </p>
        </div>
        <Button as-child><RouterLink to="/plan">Настроить обучение</RouterLink></Button>
      </CardContent>
    </Card>

    <template v-else>
      <div class="mb-4 min-h-12">
        <Alert v-if="actionMessage" class="border-neutral-300" role="status">
          <AlertDescription>{{ actionMessage }}</AlertDescription>
        </Alert>
      </div>
      <Alert v-if="sessionsError && !sessions.length" class="min-h-64 content-center">
        <AlertTitle>Не удалось открыть расписание</AlertTitle>
        <AlertDescription class="grid gap-4">
          <span>{{ sessionsError }}</span>
          <Button type="button" variant="outline" class="w-fit" @click="sessionsStore.loadSessions">
            Повторить
          </Button>
        </AlertDescription>
      </Alert>

      <Card v-else-if="!unfinishedSessions.length && !completedSessions.length">
        <CardContent
          class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center"
        >
          <div>
            <h2 class="text-lg font-semibold">Запланируйте первое занятие</h2>
            <p class="mt-2 max-w-lg text-sm text-neutral-600">
              Выберите удобные дату и время. Продолжительность первого занятия — 45 минут.
            </p>
          </div>
          <Button type="button" @click="showSchedule = true">
            <CalendarPlus /> Запланировать занятие
          </Button>
        </CardContent>
      </Card>

      <div v-else class="sessions-layout">
        <aside class="session-detail" aria-label="Выбранное занятие">
          <Card v-if="selectedSession">
            <CardHeader><CardTitle>Выбранное занятие</CardTitle></CardHeader>
            <CardContent>
              <div class="flex flex-wrap items-center justify-between gap-2">
                <Badge variant="secondary" class="rounded-md">
                  {{ selectedSession.status === 'in_progress' ? 'Идёт сейчас' : 'Следующее' }}
                </Badge>
                <span class="text-xs text-neutral-600">
                  {{ formatDate(selectedSession.startsAt) }} ·
                  {{ formatTime(selectedSession.startsAt) }}
                </span>
              </div>
              <h2 class="mt-4 mb-1 text-lg leading-snug font-semibold">
                {{ selectedSession.title }}
              </h2>
              <p class="m-0 text-xs leading-relaxed text-neutral-600">
                Цель: {{ selectedSession.courseTitle }} ·
                {{ selectedSession.durationMinutes }} минут
              </p>
              <Button
                class="mt-5 w-full"
                type="button"
                :disabled="sessionActionLoading"
                @click="runPrimary"
              >
                <Check v-if="selectedSession.status === 'in_progress'" />
                <Play v-else />
                {{ sessionActionLoading ? 'Сохраняем…' : primaryLabel }}
              </Button>
              <Button
                variant="ghost"
                class="mt-2 w-full"
                type="button"
                :disabled="sessionActionLoading"
                @click="sessionsStore.rescheduleSelectedSession"
              >
                <RotateCcw /> Перенести на завтра
              </Button>
            </CardContent>
          </Card>
          <Button variant="outline" class="w-full" type="button" @click="showSchedule = true">
            <CalendarPlus /> Добавить занятие
          </Button>
        </aside>

        <section class="agenda" aria-label="Ближайшие занятия">
          <div v-for="group in sessionGroups" :key="group.title" class="agenda__group">
            <div class="agenda__heading">
              <h2>{{ group.title }}</h2>
              <span>{{ group.items.length }}</span>
            </div>
            <Button
              v-for="session in group.items"
              :key="session.id"
              variant="outline"
              class="session-row"
              :class="{ 'session-row--selected': selectedSession?.id === session.id }"
              type="button"
              :aria-pressed="selectedSession?.id === session.id"
              @click="sessionsStore.selectSession(session.id)"
            >
              <span class="session-row__date">
                <strong>{{ formatTime(session.startsAt) }}</strong>
                <small>{{ formatDate(session.startsAt) }}</small>
              </span>
              <span class="min-w-0">
                <strong class="block text-sm leading-snug">{{ session.title }}</strong>
                <span class="mt-1 flex flex-wrap items-center gap-1 text-xs text-neutral-600">
                  <Clock3 :size="13" /> {{ session.durationMinutes }} минут
                </span>
              </span>
              <Badge variant="secondary" class="rounded-md">
                {{
                  session.status === 'in_progress'
                    ? 'Идёт'
                    : isPast(session.startsAt)
                      ? 'Просрочено'
                      : 'Запланировано'
                }}
              </Badge>
            </Button>
          </div>

          <Collapsible v-if="completedSessions.length" v-model:open="showCompleted">
            <CollapsibleTrigger as-child>
              <Button variant="outline" class="w-full justify-between" type="button">
                <span class="inline-flex items-center gap-2">
                  <History /> Завершённые занятия · {{ completedSessions.length }}
                </span>
                <ChevronDown :class="{ 'rotate-180': showCompleted }" />
              </Button>
            </CollapsibleTrigger>
            <CollapsibleContent class="completed-list">
              <div v-for="session in completedSessions" :key="session.id" class="completed-row">
                <div class="min-w-0">
                  <strong>{{ session.title }}</strong>
                  <span
                    >{{ formatDate(session.startsAt) }} · {{ session.durationMinutes }} минут</span
                  >
                </div>
                <Badge variant="secondary" class="rounded-md">Завершено</Badge>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </section>
      </div>
    </template>

    <Dialog v-model:open="showSchedule">
      <DialogContent class="sm:max-w-md">
        <DialogHeader>
          <DialogTitle>Запланировать занятие</DialogTitle>
          <DialogDescription>
            Выберите удобное время. Возьмём следующий урок выбранного стартового курса.
          </DialogDescription>
        </DialogHeader>
        <form id="schedule-form" class="grid gap-2" @submit.prevent="schedule">
          <Label for="scheduled-at">Дата и время</Label>
          <Input id="scheduled-at" v-model="scheduledAt" type="datetime-local" required />
          <p class="m-0 text-xs text-neutral-600">Продолжительность — 45 минут.</p>
        </form>
        <Alert v-if="sessionsError" class="border-neutral-300" role="alert">
          <AlertDescription>
            Не удалось сохранить занятие. Попробуйте другое время.
          </AlertDescription>
        </Alert>
        <DialogFooter>
          <Button variant="outline" type="button" @click="showSchedule = false">Отмена</Button>
          <Button
            form="schedule-form"
            type="submit"
            :disabled="!scheduledAt || sessionActionLoading"
          >
            {{ sessionActionLoading ? 'Сохраняем…' : 'Запланировать' }}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  </div>
</template>

<style scoped>
.sessions-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(300px, 340px);
  gap: 20px;
  align-items: start;
}
.agenda {
  display: grid;
  min-width: 0;
  gap: 24px;
}
.agenda__group {
  display: grid;
  min-width: 0;
  gap: 9px;
}
.agenda__heading {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding-inline: 2px;
}
.agenda__heading h2 {
  margin: 0;
  font-size: 14px;
}
.agenda__heading span {
  color: #737373;
  font-size: 12px;
}
.session-row {
  display: grid;
  grid-template-columns: 96px minmax(0, 1fr) auto;
  gap: 14px;
  align-items: center;
  width: 100%;
  height: auto;
  min-width: 0;
  padding: 14px 16px;
  color: inherit;
  background: #ffffff;
  text-align: left;
  white-space: normal;
}
.session-row:hover {
  border-color: #a3a3a3;
}
.session-row--selected {
  border-color: #737373;
  background: #fafafa;
  box-shadow: inset 3px 0 #0a0a0a;
}
.session-row__date {
  display: grid;
  gap: 2px;
  align-self: stretch;
  align-content: center;
  padding-right: 12px;
  border-right: 1px solid #e5e5e5;
}
.session-row__date strong {
  font-size: 14px;
}
.session-row__date small {
  color: #737373;
  font-size: 10px;
  line-height: 1.35;
}
.session-detail {
  position: sticky;
  top: 24px;
  display: grid;
  grid-column: 2;
  gap: 10px;
}
.completed-list {
  display: grid;
  gap: 8px;
  margin-top: 8px;
  padding: 4px 14px;
  border: 1px solid #e5e5e5;
  border-radius: 8px;
}
.completed-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 14px;
  padding: 12px 0;
  border: 1px solid #e5e5e5;
  border-radius: 6px;
}
.completed-row strong,
.completed-row span {
  display: block;
}
.completed-row strong {
  font-size: 12px;
}
.completed-row span {
  margin-top: 3px;
  color: #737373;
  font-size: 11px;
}
@media (max-width: 959px) {
  .sessions-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .session-detail {
    position: static;
    grid-row: 1;
    grid-column: 1;
  }
}
@media (max-width: 620px) {
  .session-row {
    grid-template-columns: minmax(0, 1fr);
    justify-items: start;
  }
  .session-row__date {
    width: 100%;
    padding-right: 0;
    padding-bottom: 9px;
    border-right: 0;
    border-bottom: 1px solid #e5e5e5;
  }
}
</style>
