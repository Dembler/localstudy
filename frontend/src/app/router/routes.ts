import type { RouteRecordRaw } from 'vue-router'

export const routes: RouteRecordRaw[] = [
  { path: '/', redirect: '/plan' },
  {
    path: '/plan',
    name: 'plan',
    component: () => import('@/pages/PlanPage/index.vue'),
    meta: { title: 'Сегодня' },
  },
  {
    path: '/catalog',
    name: 'catalog',
    component: () => import('@/pages/CatalogPage/index.vue'),
    meta: { title: 'Курсы' },
  },
  {
    path: '/sessions',
    name: 'sessions',
    component: () => import('@/pages/SessionsPage/index.vue'),
    meta: { title: 'Расписание' },
  },
  {
    path: '/practice',
    name: 'practice',
    component: () => import('@/pages/PracticePage/index.vue'),
    meta: { title: 'Практика' },
  },
  {
    path: '/analytics',
    name: 'analytics',
    component: () => import('@/pages/AnalyticsPage/index.vue'),
    meta: { title: 'Прогресс' },
  },
  { path: '/:pathMatch(.*)*', redirect: '/plan' },
]
