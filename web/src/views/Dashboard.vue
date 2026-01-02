<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Dashboard</h1>

    <!-- Metrics Grid -->
    <div class="grid grid-cols-1 md:grid-cols-4 gap-4 mb-6">
      <MetricCard
        title="Node Status"
        :value="health?.status || 'Unknown'"
        :variant="health?.status === 'healthy' ? 'success' : 'warning'"
      />
      <MetricCard
        title="Total Peers"
        :value="networkStats?.total_peers || 0"
      />
      <MetricCard
        title="Healthy Peers"
        :value="networkStats?.healthy_peers || 0"
        variant="success"
      />
      <MetricCard
        title="Avg Latency"
        :value="`${(networkStats?.avg_latency_ms || 0).toFixed(1)} ms`"
      />
    </div>

    <!-- Components Status -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Component Status</h2>
      <div class="grid grid-cols-3 gap-4">
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span class="text-sm font-medium text-gray-600">Blockchain</span>
          <StatusBadge :status="health?.components?.blockchain || 'unknown'" />
        </div>
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span class="text-sm font-medium text-gray-600">P2P Network</span>
          <StatusBadge :status="health?.components?.p2p_network || 'unknown'" />
        </div>
        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
          <span class="text-sm font-medium text-gray-600">Encryption</span>
          <StatusBadge :status="health?.components?.encryption || 'unknown'" />
        </div>
      </div>
    </div>

    <!-- Recent Events -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Recent Events</h2>
      <div class="space-y-2 max-h-64 overflow-y-auto">
        <div
          v-for="(event, index) in recentEvents"
          :key="index"
          class="text-sm border-l-4 pl-3 py-2"
          :class="eventBorderClass(event.type)"
        >
          <span class="font-mono text-gray-400 text-xs">
            {{ formatTime(event.timestamp) }}
          </span>
          <span class="ml-2 text-gray-700">{{ event.type }}</span>
        </div>
        <div v-if="recentEvents.length === 0" class="text-gray-500 text-center py-4">
          No recent events
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import { useWebSocket } from '@/composables/useWebSocket'
import MetricCard from '@/components/common/MetricCard.vue'
import StatusBadge from '@/components/common/StatusBadge.vue'

const store = useNodeStore()
const { health, networkStats } = storeToRefs(store)
const { events } = useWebSocket()

const recentEvents = computed(() => events.value.slice(-20).reverse())

const formatTime = (timestamp) => {
  if (!timestamp) return '--:--:--'
  return new Date(timestamp * 1000).toLocaleTimeString()
}

const eventBorderClass = (type) => {
  if (type?.startsWith('health.')) return 'border-green-500'
  if (type?.startsWith('network.')) return 'border-blue-500'
  if (type?.startsWith('token.')) return 'border-yellow-500'
  if (type?.startsWith('data.')) return 'border-purple-500'
  if (type?.startsWith('compliance.')) return 'border-orange-500'
  if (type?.startsWith('system.')) return 'border-red-500'
  return 'border-gray-300'
}

onMounted(() => {
  store.fetchHealth()
  store.fetchNetworkStats()
})
</script>
