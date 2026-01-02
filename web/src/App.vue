<template>
  <div class="min-h-screen bg-gray-100">
    <Navbar />
    <div class="flex">
      <Sidebar />
      <main class="flex-1 p-6">
        <router-view />
      </main>
    </div>

    <!-- Connection status indicator -->
    <div
      v-if="!wsConnected"
      class="fixed bottom-4 right-4 bg-red-500 text-white px-4 py-2 rounded-lg shadow-lg"
    >
      Disconnected - Reconnecting...
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted, onUnmounted, watch } from 'vue'
import { useNodeStore } from '@/stores/node'
import { useWebSocket } from '@/composables/useWebSocket'
import Navbar from '@/components/layout/Navbar.vue'
import Sidebar from '@/components/layout/Sidebar.vue'

const store = useNodeStore()
const { connected: wsConnected, events } = useWebSocket()

// Watch for WebSocket events and update store
watch(events, (newEvents) => {
  if (newEvents.length > 0) {
    const latestEvent = newEvents[newEvents.length - 1]
    store.handleEvent(latestEvent)
  }
}, { deep: true })

// Initial data fetch
onMounted(() => {
  store.fetchHealth()
  store.fetchNetworkStats()
})
</script>
