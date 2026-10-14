<script setup lang="ts">
import {
  ArrowRight,
  BookOpenCheck,
  CalendarCheck2,
  Clock3,
  Flame,
  Lightbulb,
  TrendingDown,
} from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted } from 'vue'
import { RouterLink } from 'vue-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Progress } from '@/components/ui/progress'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { useLearningWorkspaceStore } from '@/shared/stores/learning'

const workspace = useLearningWorkspaceStore()
const { plan, sessions, overview, skills, weakTopics, recommendations, loading, errors, demoMode } =
  storeToRefs(workspace)

const hasPersonalActivity = computed(
  () =>
    Boolean(plan.value?.hasActivity) || sessions.value.some((item) => item.status === 'completed'),
)
const hasProgress = computed(
  () =>
    hasPersonalActivity.value &&
    (overview.value.progress > 0 ||
      overview.value.studiedMinutes > 0 ||
      overview.value.completedSessions > 0 ||
      skills.value.length > 0 ||
      recommendations.value.length > 0),
)

const studyTimeLabel = computed(() => {
  const minutes = overview.value.studiedMinutes
  if (minutes < 60) return `${minutes} мин`
  const remainder = minutes % 60
  return `${Math.floor(minutes / 60)} ч${remainder ? ` ${remainder} мин` : ''}`
})
const streakLabel = computed(() => {
  const days = overview.value.streakDays
  const mod100 = days % 100
  const mod10 = days % 10
  const noun =
    mod100 >= 11 && mod100 <= 14 ? 'дней' : mod10 === 1 ? 'день' : mod10 < 5 ? 'дня' : 'дней'
  return `${days} ${noun}`
})

onMounted(async () => {
  workspace.clearActionMessage()
  await workspace.loadPlan()
  if (plan.value) await Promise.all([workspace.loadSessions(), workspace.loadAnalytics()])
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header__copy">
        <span class="eyebrow">Результаты обучения</span>
        <h1>Прогресс</h1>
        <p>Сначала — следующий полезный шаг, затем показатели и темы, которым нужно внимание.</p>
      </div>
    </header>

    <Card class="mb-4">
      <CardContent class="grid grid-cols-2 gap-2 p-2 sm:grid-cols-4">
        <Button as-child size="sm" variant="ghost"><RouterLink to="/plan">План</RouterLink></Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/sessions">Занятия</RouterLink>
        </Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/practice">Практика</RouterLink>
        </Button>
        <Button as-child size="sm"><RouterLink to="/analytics">Прогресс</RouterLink></Button>
      </CardContent>
    </Card>

    <Card v-if="loading.plan || (plan && (loading.analytics || loading.sessions))" class="min-h-72">
      <CardContent class="grid min-h-72 content-center gap-4 p-6 sm:grid-cols-2">
        <Skeleton class="h-40 w-full" /><Skeleton class="h-40 w-full" />
        <Skeleton class="h-20 w-full sm:col-span-2" />
      </CardContent>
    </Card>
    <Card v-else-if="!plan">
      <CardContent class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center">
        <div>
          <h2 class="text-lg font-semibold">Сначала настройте обучение</h2>
          <p class="mt-2 max-w-lg text-sm text-neutral-600">
            Прогресс появится после занятий и практических попыток по вашему плану.
          </p>
        </div>
        <Button as-child><RouterLink to="/plan">Настроить обучение</RouterLink></Button>
      </CardContent>
    </Card>
    <Alert v-else-if="errors.analytics && !skills.length" class="min-h-64 content-center">
      <AlertTitle>Не удалось открыть прогресс</AlertTitle>
      <AlertDescription class="grid gap-4">
        <span>{{ errors.analytics }}</span
        ><Button variant="outline" class="w-fit" @click="workspace.loadAnalytics">
          Повторить
        </Button>
      </AlertDescription>
    </Alert>

    <Card v-else-if="!hasProgress">
      <CardContent class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center">
        <div>
          <h2 class="text-lg font-semibold">Прогресс появится после первого шага</h2>
          <p class="mt-2 max-w-lg text-sm text-neutral-600">
            Завершите занятие или отправьте ответ в практике. Тогда здесь появятся время, навыки и
            рекомендации.
          </p>
        </div>
        <Button as-child><RouterLink to="/plan">Вернуться к шагу на сегодня</RouterLink></Button>
      </CardContent>
    </Card>

    <template v-else>
      <Alert v-if="errors.analytics" class="mb-4 border-neutral-300" role="status">
        <AlertDescription>
          Часть показателей не удалось обновить. Ниже оставлены только полученные данные.
        </AlertDescription>
      </Alert>
      <Alert class="mb-4 border-neutral-300 bg-neutral-50" role="note">
        <AlertDescription class="leading-relaxed">
          Показатели собраны по всей активности в этом локальном профиле и могут включать другие
          учебные цели.
        </AlertDescription>
      </Alert>
      <Alert v-if="demoMode.analytics" class="mb-4 border-neutral-300">
        <AlertTitle>Показаны демонстрационные данные</AlertTitle>
        <AlertDescription>
          Не удалось обновить ваши показатели. Ниже показан пример, а не личный прогресс.
        </AlertDescription>
      </Alert>
      <Card>
        <CardHeader>
          <CardTitle>Следующий шаг</CardTitle>
          <CardDescription>
            Рекомендация на основе общей активности этого локального профиля.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div v-if="recommendations[0]" class="recommendation">
            <span class="grid size-10 shrink-0 place-items-center rounded-md border bg-neutral-50"
              ><Lightbulb :size="20"
            /></span>
            <div class="min-w-0">
              <Badge variant="secondary" class="rounded-md">Рекомендуем</Badge>
              <h2 class="mt-3 mb-1 text-lg leading-snug font-semibold">
                {{ recommendations[0].title }}
              </h2>
              <p class="m-0 text-sm leading-relaxed text-neutral-600">
                {{ recommendations[0].reason }}
              </p>
              <div class="mt-3 flex flex-wrap gap-x-5 gap-y-1 text-xs text-neutral-600">
                <span>{{ recommendations[0].topic }}</span>
                <span>{{ recommendations[0].estimatedMinutes }} минут</span>
              </div>
            </div>
            <Button as-child class="recommendation__action">
              <RouterLink :to="recommendations[0].to">
                {{
                  recommendations[0].to === '/sessions'
                    ? 'Открыть расписание'
                    : 'Перейти к практике'
                }}
                <ArrowRight />
              </RouterLink>
            </Button>
          </div>
          <div v-else class="recommendation recommendation--empty">
            <span class="grid size-10 shrink-0 place-items-center rounded-md border bg-neutral-50"
              ><Lightbulb :size="20"
            /></span>
            <div class="min-w-0">
              <h2 class="m-0 text-base font-semibold">Закрепите изученное</h2>
              <p class="mt-1 mb-0 text-sm text-neutral-600">
                Следующая практика поможет уточнить, какие темы уже усвоены.
              </p>
            </div>
            <Button as-child class="recommendation__action">
              <RouterLink to="/practice">Перейти к практике <ArrowRight /></RouterLink>
            </Button>
          </div>
        </CardContent>
      </Card>

      <section class="metrics-grid" aria-label="Сводные показатели">
        <Card class="metric-item">
          <CardContent class="grid gap-1.5 p-4">
            <BookOpenCheck :size="18" /><span>Общий прогресс</span
            ><strong>{{ overview.progress }}%</strong
            ><small>доля завершённых уроков во всех планах</small>
          </CardContent>
        </Card>
        <Card class="metric-item">
          <CardContent class="grid gap-1.5 p-4">
            <Clock3 :size="18" /><span>Время обучения</span><strong>{{ studyTimeLabel }}</strong
            ><small>фактическое время за период</small>
          </CardContent>
        </Card>
        <Card class="metric-item">
          <CardContent class="grid gap-1.5 p-4">
            <CalendarCheck2 :size="18" /><span>Завершено</span
            ><strong>{{ overview.completedSessions }}</strong
            ><small>учебных сессий за период</small>
          </CardContent>
        </Card>
        <Card class="metric-item">
          <CardContent class="grid gap-1.5 p-4">
            <Flame :size="18" /><span>Текущая серия</span><strong>{{ streakLabel }}</strong
            ><small>дней обучения подряд</small>
          </CardContent>
        </Card>
      </section>

      <div class="analytics-layout">
        <Card>
          <CardHeader>
            <CardTitle>Навыки</CardTitle
            ><CardDescription>
              Оценка основана на уроках, практике и последних попытках.
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid gap-5">
              <div v-for="skill in skills" :key="skill.id" class="min-w-0">
                <strong class="mb-2 block text-sm leading-snug">{{ skill.name }}</strong>
                <div class="grid gap-2">
                  <div class="flex items-center justify-between text-xs">
                    <span>Освоено</span><strong>{{ skill.value }}%</strong>
                  </div>
                  <Progress
                    :model-value="skill.value"
                    :aria-label="`Прогресс навыка: ${skill.name}`"
                  />
                </div>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle>Темы для внимания</CardTitle
            ><CardDescription> Сначала показаны темы с самым низким результатом. </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="grid">
              <div v-for="(topic, index) in weakTopics" :key="topic.id" class="weak-row">
                <span
                  class="grid size-9 shrink-0 place-items-center rounded-md border bg-neutral-50"
                  ><TrendingDown :size="17"
                /></span>
                <div class="min-w-0">
                  <strong class="block text-sm leading-snug">{{ topic.title }}</strong>
                  <p class="mt-1 mb-0 text-xs leading-relaxed text-neutral-600">
                    {{ topic.reason }}
                  </p>
                </div>
                <Badge variant="outline" class="weak-row__score rounded-md">
                  {{ topic.score }}%
                </Badge>
                <Separator v-if="index < weakTopics.length - 1" class="weak-row__separator" />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>

<style scoped>
.recommendation {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 16px;
  align-items: start;
}
.recommendation__action {
  align-self: center;
}
.metrics-grid {
  display: grid;
  grid-template-columns: repeat(4, minmax(0, 1fr));
  gap: 12px;
  margin: 16px 0;
}
.metric-item {
  min-width: 0;
}
.metric-item [data-slot='card-content'] > span {
  color: #525252;
  font-size: 12px;
  font-weight: 500;
}
.metric-item [data-slot='card-content'] > strong {
  font-size: 22px;
  line-height: 1.2;
  letter-spacing: -0.03em;
}
.metric-item [data-slot='card-content'] > small {
  color: #525252;
  font-size: 12px;
  line-height: 1.4;
}
.analytics-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(0, 1fr);
  gap: 16px;
  align-items: start;
}
.weak-row {
  display: grid;
  grid-template-columns: auto minmax(0, 1fr) auto;
  gap: 12px;
  align-items: center;
}
.weak-row__separator {
  grid-column: 1 / -1;
  margin: 14px 0;
}
@media (max-width: 959px) {
  .recommendation {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .recommendation__action {
    grid-column: 2;
    justify-self: start;
  }
  .metrics-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
  }
  .analytics-layout {
    grid-template-columns: minmax(0, 1fr);
  }
}
@media (max-width: 520px) {
  .recommendation {
    grid-template-columns: minmax(0, 1fr);
  }
  .recommendation__action {
    grid-column: 1;
    width: 100%;
  }
  .metrics-grid {
    grid-template-columns: minmax(0, 1fr);
  }
  .metric-item {
    min-height: 0;
  }
  .weak-row {
    grid-template-columns: auto minmax(0, 1fr);
  }
  .weak-row__score {
    grid-column: 2;
    justify-self: start;
  }
}
</style>
