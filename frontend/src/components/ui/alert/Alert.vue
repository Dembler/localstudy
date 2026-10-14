<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import type { AlertVariants } from '.'
import { cn } from '@/lib/utils'
import { alertVariants } from '.'

const props = defineProps<{
  class?: HTMLAttributes['class']
  variant?: AlertVariants['variant']
  role?: 'alert' | 'note' | 'status'
}>()
</script>

<template>
  <div
    data-slot="alert"
    :class="cn(alertVariants({ variant }), props.class)"
    :role="props.role ?? (variant === 'destructive' ? 'alert' : undefined)"
  >
    <slot />
  </div>
</template>
