<template>
  <div :class="['card', variantClass]">
    <div class="text-sm font-medium text-gray-500">{{ title }}</div>
    <div class="mt-1 text-2xl font-semibold" :class="valueClass">
      {{ value }}
    </div>
    <div v-if="subtitle" class="mt-1 text-xs text-gray-400">
      {{ subtitle }}
    </div>
  </div>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  title: {
    type: String,
    required: true
  },
  value: {
    type: [String, Number],
    required: true
  },
  subtitle: {
    type: String,
    default: null
  },
  variant: {
    type: String,
    default: 'default',
    validator: (v) => ['default', 'success', 'warning', 'error'].includes(v)
  }
})

const variantClass = computed(() => {
  const classes = {
    success: 'border-l-4 border-green-500',
    warning: 'border-l-4 border-yellow-500',
    error: 'border-l-4 border-red-500',
    default: ''
  }
  return classes[props.variant]
})

const valueClass = computed(() => {
  const classes = {
    success: 'text-green-600',
    warning: 'text-yellow-600',
    error: 'text-red-600',
    default: 'text-gray-900'
  }
  return classes[props.variant]
})
</script>
