import { readFileSync } from 'node:fs'
import { stdout } from 'node:process'
import { fileURLToPath, URL } from 'node:url'

const root = fileURLToPath(new URL('../src/shared/api/', import.meta.url))
const groups = {
  'catalog.ts': [
    'listCourses',
    'searchCourses',
    'getCourse',
    'getCoursePrerequisites',
    'getLessonPreview',
  ],
  'plans.ts': [
    'createPlan',
    'updatePlanWorkload',
    'addPlanGoal',
    'rebalancePlan',
    'getPlanForecast',
    'deletePlan',
    'deletePlanGoal',
    'removePlanCourse',
  ],
  'sessions.ts': [
    'getSessionCalendar',
    'scheduleSession',
    'startSession',
    'completeSession',
    'rescheduleSession',
    'deleteSession',
  ],
  'practice.ts': [
    'getNextAssignment',
    'submitAttempt',
    'requestHint',
    'retryAssignment',
    'listAttempts',
  ],
  'analytics.ts': ['getOverview', 'getSkills', 'getStreak', 'getWeakTopics', 'getRecommendations'],
}

let count = 0
for (const [file, operations] of Object.entries(groups)) {
  const source = readFileSync(`${root}${file}`, 'utf8')
  for (const operation of operations) {
    if (!source.includes(`export async function ${operation}`)) {
      throw new Error(`${file}: отсутствует операция ${operation}`)
    }
    count += 1
  }
}

if (count !== 29) throw new Error(`Ожидалось 29 бизнес-операций, найдено ${count}`)

const health = readFileSync(`${root}health.ts`, 'utf8')
if (!health.includes('export async function getHealth')) {
  throw new Error('Техническая health-операция отсутствует')
}

stdout.write('API contract OK: 29 business operations + health\n')
