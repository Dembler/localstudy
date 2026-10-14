export interface UiCourse {
  id: string
  title: string
  description: string
  level: string
  durationHours: number
  lessonsCount: number
  skills: string[]
  category: string
  progress?: number
}

export interface UiMilestone {
  id: string
  title: string
  courseTitle: string
  dueLabel: string
  status: 'done' | 'current' | 'next'
  durationMinutes: number
}

export interface UiPlan {
  id: string
  title: string
  courseId?: string
  startDate?: string
  hasActivity?: boolean
  weeklyMinutes: number
  progress: number
  forecastDate: string
  milestones: UiMilestone[]
}

export interface UiSession {
  id: string
  planId: string
  title: string
  courseTitle: string
  startsAt: string
  durationMinutes: number
  status: 'scheduled' | 'in_progress' | 'completed' | 'cancelled'
}

export interface UiAssignment {
  id: string
  lessonId: string
  title: string
  topic: string
  prompt: string
  difficulty: string
  estimatedMinutes: number
  answerPlaceholder: string
  hint?: string
}

export interface UiAttempt {
  id: string
  submittedAt: string
  isCorrect: boolean
  score: number
  answer: string
  feedback: string
}

export interface UiSkill {
  id: string
  name: string
  value: number
  trend: number
}

export interface UiRecommendation {
  id: string
  title: string
  reason: string
  topic: string
  estimatedMinutes: number
  to: '/practice' | '/sessions'
}

export const demoCourses: UiCourse[] = [
  {
    id: 'python-foundations',
    title: 'Python: уверенные основы и чистый код',
    description: 'От базового синтаксиса до небольших программ с понятной структурой и тестами.',
    level: 'Начальный',
    durationHours: 18,
    lessonsCount: 24,
    skills: ['Синтаксис', 'Функции', 'Тестирование'],
    category: 'Разработка',
    progress: 42,
  },
  {
    id: 'sql-practice',
    title: 'SQL для практических задач аналитики',
    description: 'Запросы, соединения и оконные функции на примерах из продуктовой аналитики.',
    level: 'Средний',
    durationHours: 14,
    lessonsCount: 19,
    skills: ['SQL', 'Аналитика', 'Моделирование данных'],
    category: 'Данные',
  },
  {
    id: 'algorithms',
    title: 'Алгоритмы без лишней теории',
    description: 'Структуры данных и алгоритмические приёмы с пошаговыми визуальными разборами.',
    level: 'Средний',
    durationHours: 22,
    lessonsCount: 28,
    skills: ['Алгоритмы', 'Структуры данных', 'Оценка сложности'],
    category: 'Разработка',
  },
  {
    id: 'web-api',
    title: 'Проектирование надёжных Web API',
    description: 'Контракты, ошибки, версионирование и тестирование HTTP-интерфейсов.',
    level: 'Продвинутый',
    durationHours: 12,
    lessonsCount: 16,
    skills: ['HTTP', 'REST', 'Контрактное тестирование'],
    category: 'Архитектура',
  },
]

export const demoPlan: UiPlan = {
  id: 'demo-plan',
  title: 'Стать увереннее в серверной разработке',
  weeklyMinutes: 240,
  progress: 38,
  forecastDate: '18 декабря',
  milestones: [
    {
      id: 'milestone-1',
      title: 'Функции, параметры и возвращаемые значения',
      courseTitle: 'Python: уверенные основы',
      dueLabel: 'Завершено вчера',
      status: 'done',
      durationMinutes: 35,
    },
    {
      id: 'milestone-2',
      title: 'Практика: разложить задачу на небольшие функции',
      courseTitle: 'Python: уверенные основы',
      dueLabel: 'Сегодня, 19:00',
      status: 'current',
      durationMinutes: 45,
    },
    {
      id: 'milestone-3',
      title: 'Типы данных и проверка входных значений',
      courseTitle: 'Проектирование надёжных Web API',
      dueLabel: 'Пятница',
      status: 'next',
      durationMinutes: 40,
    },
    {
      id: 'milestone-4',
      title: 'Первый контракт метода API и сценарии ошибок',
      courseTitle: 'Проектирование надёжных Web API',
      dueLabel: 'Воскресенье',
      status: 'next',
      durationMinutes: 50,
    },
  ],
}

const dateAt = (dayOffset: number, hour: number, minute = 0) => {
  const date = new Date()
  date.setDate(date.getDate() + dayOffset)
  date.setHours(hour, minute, 0, 0)
  return date.toISOString()
}

export const demoSessions: UiSession[] = [
  {
    id: 'session-1',
    planId: 'demo-plan',
    title: 'Практика с функциями',
    courseTitle: 'Python: уверенные основы',
    startsAt: dateAt(0, 19),
    durationMinutes: 45,
    status: 'scheduled',
  },
  {
    id: 'session-2',
    planId: 'demo-plan',
    title: 'Разбор JOIN на реальном датасете',
    courseTitle: 'SQL для практических задач аналитики',
    startsAt: dateAt(2, 18, 30),
    durationMinutes: 50,
    status: 'scheduled',
  },
  {
    id: 'session-3',
    planId: 'demo-plan',
    title: 'HTTP-ошибки и единый формат ответа',
    courseTitle: 'Проектирование надёжных Web API',
    startsAt: dateAt(4, 11),
    durationMinutes: 40,
    status: 'scheduled',
  },
]

export const demoAssignment: UiAssignment = {
  id: 'assignment-1',
  lessonId: 'lesson-1',
  title: 'Нормализация списка оценок',
  topic: 'Функции и коллекции',
  prompt:
    'Напишите функцию normalize_scores, которая принимает список чисел от 0 до 100 и возвращает новый список значений от 0 до 1. Пустой список должен возвращаться без ошибки.',
  difficulty: 'Базовая практика',
  estimatedMinutes: 15,
  answerPlaceholder: 'Введите короткий ответ',
  hint: 'Начните с обработки пустого списка, затем разделите каждый элемент на 100.',
}

export const demoAttempts: UiAttempt[] = [
  {
    id: 'attempt-1',
    submittedAt: new Date(Date.now() - 86_400_000).toISOString(),
    isCorrect: false,
    score: 70,
    answer: 'return [score / 100 for score in scores]',
    feedback: 'Основная идея верна. Добавьте явную проверку типов входных значений.',
  },
]

export const demoSkills: UiSkill[] = [
  { id: 'skill-1', name: 'Функции и декомпозиция', value: 72, trend: 8 },
  { id: 'skill-2', name: 'Работа с коллекциями', value: 64, trend: 4 },
  { id: 'skill-3', name: 'Тестирование', value: 41, trend: -2 },
  { id: 'skill-4', name: 'Проектирование API', value: 36, trend: 6 },
]

export const demoRecommendations: UiRecommendation[] = [
  {
    id: 'recommendation-1',
    title: 'Повторить граничные случаи в функциях',
    reason: 'В двух последних попытках были пропущены пустые входные значения.',
    topic: 'Тестирование функций',
    estimatedMinutes: 20,
    to: '/practice',
  },
  {
    id: 'recommendation-2',
    title: 'Закрепить работу со словарями',
    reason: 'Тема нужна для следующего модуля и пока изучена на 48%.',
    topic: 'Коллекции Python',
    estimatedMinutes: 25,
    to: '/practice',
  },
]
