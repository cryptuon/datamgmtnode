<template>
  <nav class="bg-white shadow-sm border-b border-gray-200">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <div class="flex justify-between h-16">
        <div class="flex items-center">
          <div class="flex-shrink-0 flex items-center">
            <svg class="h-8 w-8 text-primary-600" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                d="M5 12h14M5 12a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v4a2 2 0 01-2 2M5 12a2 2 0 00-2 2v4a2 2 0 002 2h14a2 2 0 002-2v-4a2 2 0 00-2-2m-2-4h.01M17 16h.01" />
            </svg>
            <span class="ml-2 text-xl font-bold text-gray-900">DataMgmt Node</span>
          </div>
        </div>

        <div class="flex items-center space-x-4">
          <!-- Connection status -->
          <div class="flex items-center">
            <span
              :class="[
                'w-2 h-2 rounded-full mr-2',
                wsConnected ? 'bg-green-500' : 'bg-red-500'
              ]"
            ></span>
            <span class="text-sm text-gray-500">
              {{ wsConnected ? 'Connected' : 'Disconnected' }}
            </span>
          </div>

          <!-- Health status -->
          <div v-if="health" class="flex items-center">
            <span
              :class="[
                'status-badge',
                health.status === 'healthy' ? 'healthy' : 'degraded'
              ]"
            >
              {{ health.status }}
            </span>
          </div>
        </div>
      </div>
    </div>
  </nav>
</template>

<script setup>
import { computed } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import { useWebSocket } from '@/composables/useWebSocket'

const store = useNodeStore()
const { health } = storeToRefs(store)
const { connected: wsConnected } = useWebSocket()
</script>
