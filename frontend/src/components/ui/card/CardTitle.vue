<script setup lang="ts">
import type { PrimitiveProps } from 'reka-ui'
import type { HTMLAttributes } from 'vue'
import { Primitive } from 'reka-ui'
import { cn } from '@/lib/utils'

const props = withDefaults(
  defineProps<{
    as?: PrimitiveProps['as']
    class?: HTMLAttributes['class']
  }>(),
  {
    as: 'h2',
  },
)
</script>

<template>
  <Primitive
    :as="as"
    data-slot="card-title"
    :class="
      cn(
        'text-base leading-snug font-medium group-data-[size=sm]/card:text-sm cn-font-heading',
        props.class,
      )
    "
  >
    <slot />
  </Primitive>
</template>
