<template>
  <span :class="['status-badge', statusClass]">
    {{ displayStatus }}
  </span>
</template>

<script setup>
import { computed } from 'vue'

const props = defineProps({
  status: {
    type: String,
    required: true
  },
  label: {
    type: String,
    default: null
  }
})

const displayStatus = computed(() => {
  return props.label || props.status.charAt(0).toUpperCase() + props.status.slice(1)
})

const statusClass = computed(() => {
  const statusMap = {
    healthy: 'healthy',
    connected: 'connected',
    running: 'running',
    initialized: 'healthy',
    degraded: 'degraded',
    disconnected: 'disconnected',
    stopped: 'stopped',
    unhealthy: 'unhealthy',
    error: 'unhealthy'
  }
  return statusMap[props.status.toLowerCase()] || 'degraded'
})
</script>
