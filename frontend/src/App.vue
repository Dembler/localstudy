<script setup lang="ts">
import { BarChart3, BookMarked, CalendarDays, ClipboardCheck, Library } from '@lucide/vue'
import { RouterLink, RouterView } from 'vue-router'

import { Button } from '@/components/ui/button'
import { Toaster } from '@/components/ui/sonner'

const navigation = [
  { to: '/plan', label: 'Сегодня', icon: ClipboardCheck, group: 'Учёба' },
  { to: '/sessions', label: 'Расписание', icon: CalendarDays, group: 'Учёба' },
  { to: '/practice', label: 'Практика', icon: BookMarked, group: 'Учёба' },
  { to: '/catalog', label: 'Курсы', icon: Library, group: 'Развитие' },
  { to: '/analytics', label: 'Прогресс', icon: BarChart3, group: 'Развитие' },
]

const groups = ['Учёба', 'Развитие'] as const
</script>

<template>
  <div class="app-shell">
    <aside class="sidebar" aria-label="Основная навигация">
      <RouterLink class="brand" to="/plan" aria-label="LocalStudy — сегодня">
        <span class="brand__mark"><BookMarked :size="17" /></span>
        <span class="brand__copy">
          <strong>LocalStudy</strong>
          <small>учебная система</small>
        </span>
      </RouterLink>

      <nav class="sidebar__nav" aria-label="Разделы">
        <div v-for="group in groups" :key="group" class="sidebar__group">
          <span class="sidebar__group-label">{{ group }}</span>
          <Button
            v-for="item in navigation.filter((entry) => entry.group === group)"
            :key="item.to"
            as-child
            variant="ghost"
            class="h-10 w-full justify-start px-2"
          >
            <RouterLink class="nav-link" :to="item.to">
              <component :is="item.icon" :size="18" />
              <span>{{ item.label }}</span>
            </RouterLink>
          </Button>
        </div>
      </nav>
    </aside>

    <header class="mobile-header">
      <RouterLink class="brand brand--mobile" to="/plan">
        <span class="brand__mark"><BookMarked :size="16" /></span>
        <strong>LocalStudy</strong>
      </RouterLink>
      <span class="mobile-header__caption">Ваш маршрут обучения</span>
    </header>

    <main class="main-content">
      <RouterView />
    </main>

    <nav class="bottom-nav" aria-label="Основная навигация">
      <Button
        v-for="item in navigation"
        :key="item.to"
        as-child
        variant="ghost"
        class="h-auto min-w-0 rounded-md p-0"
      >
        <RouterLink class="bottom-nav__link" :to="item.to">
          <component :is="item.icon" :size="19" />
          <span>{{ item.label }}</span>
        </RouterLink>
      </Button>
    </nav>

    <Toaster position="top-right" />
  </div>
</template>
