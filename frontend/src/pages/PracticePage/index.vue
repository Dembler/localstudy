<script setup lang="ts">
import { ArrowRight, Check, ChevronDown, Clock3, History, Lightbulb, RotateCcw } from '@lucide/vue'
import { storeToRefs } from 'pinia'
import { computed, onMounted, ref } from 'vue'
import { RouterLink } from 'vue-router'

import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible'
import { Label } from '@/components/ui/label'
import { Separator } from '@/components/ui/separator'
import { Skeleton } from '@/components/ui/skeleton'
import { Textarea } from '@/components/ui/textarea'
import { usePlanStore } from '@/shared/stores/plans'
import { usePracticeStore } from '@/shared/stores/practice'
import { useNoticesStore } from '@/shared/stores/notices'

const plansStore = usePlanStore()
const { plan, loading: planLoading } = storeToRefs(plansStore)
const practiceStore = usePracticeStore()
const {
  assignment,
  attempts,
  visibleHint,
  lastAttemptFeedback,
  loading: practiceLoading,
  actionLoading: practiceActionLoading,
  error: practiceError,
} = storeToRefs(practiceStore)
const noticesStore = useNoticesStore()

const answer = ref('')
const showHistory = ref(false)
const feedbackShown = ref(false)

const latestAttempt = computed(() => attempts.value[0] ?? null)
const answerWasCorrect = computed(() => latestAttempt.value?.isCorrect ?? false)

const submit = async () => {
  if (!answer.value.trim()) return
  const countBefore = attempts.value.length
  await practiceStore.submitPracticeAnswer(answer.value)
  feedbackShown.value = attempts.value.length > countBefore
}

const editAnswer = () => {
  feedbackShown.value = false
}

const requestAnother = async () => {
  await practiceStore.retryPracticeAssignment()
  if (!practiceError.value) {
    answer.value = ''
    feedbackShown.value = false
  }
}

const formatDate = (value: string) =>
  new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))

onMounted(async () => {
  noticesStore.clearActionMessage()
  await plansStore.loadPlan()
  if (plan.value) await practiceStore.loadPractice()
})
</script>

<template>
  <div class="page">
    <header class="page-header">
      <div class="page-header__copy">
        <span class="eyebrow">Закрепление</span>
        <h1>Практика</h1>
        <p>Один вопрос за раз: ответьте, проверьте результат и выберите следующий шаг.</p>
      </div>
    </header>

    <Card class="mb-4">
      <CardContent class="grid grid-cols-2 gap-2 p-2 sm:grid-cols-4">
        <Button as-child size="sm" variant="ghost"><RouterLink to="/plan">План</RouterLink></Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/sessions">Занятия</RouterLink>
        </Button>
        <Button as-child size="sm"><RouterLink to="/practice">Практика</RouterLink></Button>
        <Button as-child size="sm" variant="ghost">
          <RouterLink to="/analytics">Прогресс</RouterLink>
        </Button>
      </CardContent>
    </Card>

    <Card v-if="planLoading || (plan && practiceLoading)" class="min-h-72">
      <CardContent
        class="grid min-h-72 content-center gap-4 p-6 sm:grid-cols-[minmax(0,1fr)_280px]"
      >
        <div class="grid gap-3">
          <Skeleton class="h-7 w-2/3" /><Skeleton class="h-24 w-full" /><Skeleton
            class="h-32 w-full"
          />
        </div>
        <Skeleton class="h-full min-h-48 w-full" />
      </CardContent>
    </Card>

    <Card v-else-if="!plan">
      <CardContent class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center">
        <div>
          <h2 class="text-lg font-semibold">Сначала настройте обучение</h2>
          <p class="mt-2 text-sm text-neutral-600">
            Практика подбирается по курсам вашего учебного плана.
          </p>
        </div>
        <Button as-child><RouterLink to="/plan">Настроить обучение</RouterLink></Button>
      </CardContent>
    </Card>

    <Alert v-else-if="practiceError && !assignment" class="min-h-64 content-center">
      <AlertTitle>Не удалось открыть практику</AlertTitle>
      <AlertDescription class="grid gap-4">
        <span>{{ practiceError }}</span
        ><Button variant="outline" class="w-fit" @click="practiceStore.loadPractice">
          Повторить
        </Button>
      </AlertDescription>
    </Alert>

    <Card v-else-if="!assignment">
      <CardContent class="flex min-h-64 flex-col items-center justify-center gap-4 p-6 text-center">
        <div>
          <h2 class="text-lg font-semibold">Заданий пока нет</h2>
          <p class="mt-2 max-w-lg text-sm text-neutral-600">
            Завершите первое занятие — после него здесь появится подходящая практика.
          </p>
        </div>
        <Button as-child><RouterLink to="/sessions">Перейти к расписанию</RouterLink></Button>
      </CardContent>
    </Card>

    <div v-else class="practice-layout">
      <section class="min-w-0" aria-label="Текущее задание">
        <Card>
          <CardContent class="pt-6">
            <div class="exercise-heading">
              <div class="min-w-0">
                <span class="eyebrow">Условие</span>
                <h2>{{ assignment.title }}</h2>
              </div>
              <Badge variant="secondary" class="rounded-md">{{ assignment.difficulty }}</Badge>
            </div>
            <div class="mt-3 flex flex-wrap gap-x-4 gap-y-1 text-xs text-neutral-600">
              <span>{{ assignment.topic }}</span>
              <span class="inline-flex items-center gap-1.5">
                <Clock3 :size="14" /> около {{ assignment.estimatedMinutes }} минут
              </span>
            </div>
            <Alert class="my-5 bg-neutral-50" role="note">
              <AlertTitle>Задание</AlertTitle>
              <AlertDescription class="leading-relaxed">{{ assignment.prompt }}</AlertDescription>
            </Alert>

            <Alert v-if="visibleHint" class="mb-5 border-neutral-300 bg-neutral-50" role="status">
              <Lightbulb />
              <AlertTitle>Подсказка</AlertTitle>
              <AlertDescription class="leading-relaxed">{{ visibleHint }}</AlertDescription>
            </Alert>

            <template v-if="!feedbackShown">
              <form class="grid gap-4" @submit.prevent="submit">
                <div class="grid gap-2">
                  <Label for="answer">Ваш ответ</Label>
                  <Textarea
                    id="answer"
                    v-model="answer"
                    class="min-h-40 bg-neutral-50"
                    :placeholder="assignment.answerPlaceholder"
                  />
                </div>

                <Alert v-if="practiceError" class="border-neutral-300" role="alert">
                  <AlertDescription>
                    Ответ не отправлен. Текст остался в форме — попробуйте ещё раз.
                  </AlertDescription>
                </Alert>

                <div class="answer-actions">
                  <div>
                    <Button
                      variant="outline"
                      type="button"
                      :disabled="practiceActionLoading"
                      @click="practiceStore.requestPracticeHint"
                    >
                      <Lightbulb /> Показать подсказку
                    </Button>
                    <span>Подсказка снизит максимальный балл за попытку.</span>
                  </div>
                  <Button
                    class="answer-submit"
                    type="submit"
                    :disabled="!answer.trim() || practiceActionLoading"
                  >
                    <Check />
                    {{ practiceActionLoading ? 'Проверяем…' : 'Проверить ответ' }}
                  </Button>
                </div>
              </form>
            </template>

            <Alert v-else class="feedback" role="status">
              <Badge variant="secondary" class="h-10 rounded-md px-3">
                <Check :size="20" /> Результат
              </Badge>
              <div class="min-w-0">
                <h3>{{ answerWasCorrect ? 'Ответ верный' : 'Стоит попробовать ещё раз' }}</h3>
                <p>{{ lastAttemptFeedback }}</p>
                <strong>{{ latestAttempt?.score ?? 0 }} баллов из 100</strong>
              </div>
              <div class="feedback__actions">
                <Button v-if="answerWasCorrect" as-child>
                  <RouterLink to="/analytics">Посмотреть прогресс <ArrowRight /></RouterLink>
                </Button>
                <Button v-else type="button" @click="editAnswer">
                  Исправить ответ <ArrowRight />
                </Button>
                <Button
                  variant="outline"
                  type="button"
                  :disabled="practiceActionLoading"
                  @click="requestAnother"
                >
                  <RotateCcw /> Начать новую попытку
                </Button>
              </div>
            </Alert>
          </CardContent>
        </Card>
      </section>

      <aside class="practice-aside">
        <Card>
          <CardHeader><CardTitle>Ваши попытки</CardTitle></CardHeader>
          <CardContent>
            <div class="attempt-summary">
              <Card>
                <CardContent class="p-3">
                  <strong>{{ attempts.length }}</strong>
                  <span>всего</span>
                </CardContent>
              </Card>
              <Card>
                <CardContent class="p-3">
                  <strong>{{ Math.max(0, ...attempts.map((item) => item.score)) }}%</strong>
                  <span>лучший результат</span>
                </CardContent>
              </Card>
            </div>
            <Collapsible v-model:open="showHistory" class="mt-4">
              <CollapsibleTrigger as-child>
                <Button variant="outline" class="w-full justify-between" type="button">
                  <span class="inline-flex items-center gap-2"><History /> История</span>
                  <ChevronDown :class="{ 'rotate-180': showHistory }" />
                </Button>
              </CollapsibleTrigger>
              <CollapsibleContent>
                <ol class="history-list">
                  <li v-for="attempt in attempts" :key="attempt.id">
                    <div>
                      <span>{{ formatDate(attempt.submittedAt) }}</span>
                      <strong>{{ attempt.score }}%</strong>
                    </div>
                    <p>{{ attempt.feedback }}</p>
                    <Separator />
                  </li>
                </ol>
              </CollapsibleContent>
            </Collapsible>
          </CardContent>
        </Card>
      </aside>
    </div>
  </div>
</template>

<style scoped>
.practice-layout {
  display: grid;
  grid-template-columns: minmax(0, 1fr) minmax(260px, 310px);
  gap: 20px;
  align-items: start;
}
.exercise-heading {
  display: flex;
  min-width: 0;
  align-items: flex-start;
  justify-content: space-between;
  gap: 14px;
}
.exercise-heading h2 {
  margin: 0;
  font-size: 21px;
  line-height: 1.25;
  letter-spacing: -0.025em;
}
.answer-actions {
  display: flex;
  align-items: end;
  justify-content: space-between;
  gap: 16px;
}
.answer-actions > div {
  display: grid;
  gap: 5px;
}
.answer-actions span {
  color: #737373;
  font-size: 10px;
  line-height: 1.35;
}
.feedback {
  display: grid;
  grid-template-columns: 112px minmax(0, 1fr);
  gap: 14px;
  background: #fafafa;
}
.feedback h3 {
  margin: 0;
  font-size: 18px;
}
.feedback p {
  margin: 7px 0;
  color: #525252;
  font-size: 13px;
  line-height: 1.6;
}
.feedback__actions {
  display: flex;
  grid-column: 2;
  flex-wrap: wrap;
  gap: 8px;
  margin-top: 6px;
}
.practice-aside {
  position: sticky;
  top: 24px;
}
.attempt-summary {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 8px;
}
.attempt-summary strong,
.attempt-summary span {
  display: block;
}
.attempt-summary strong {
  font-size: 18px;
}
.attempt-summary span {
  margin-top: 2px;
  color: #737373;
  font-size: 10px;
}
.history-list {
  display: grid;
  gap: 12px;
  margin: 14px 0 0;
  padding: 0;
  list-style: none;
}
.history-list li > div {
  display: flex;
  justify-content: space-between;
  gap: 10px;
  color: #737373;
  font-size: 11px;
}
.history-list li > div strong {
  color: #0a0a0a;
}
.history-list p {
  margin: 5px 0 10px;
  color: #525252;
  font-size: 11px;
  line-height: 1.5;
}
@media (max-width: 959px) {
  .practice-layout {
    grid-template-columns: minmax(0, 1fr);
  }
  .practice-aside {
    position: static;
  }
  .answer-actions,
  .feedback__actions {
    display: grid;
    grid-template-columns: minmax(0, 1fr);
  }
  .answer-actions > *,
  .answer-actions button,
  .feedback__actions > * {
    width: 100%;
  }
  .answer-submit {
    order: -1;
  }
  .feedback {
    grid-template-columns: minmax(0, 1fr);
  }
  .feedback__actions {
    grid-column: 1;
  }
}
</style>
