<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Network</h1>

    <!-- Stats Cards -->
    <div class="grid grid-cols-1 md:grid-cols-3 gap-4 mb-6">
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

    <!-- Peer List -->
    <div class="card">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Connected Peers</h2>
        <label class="flex items-center gap-2 text-sm text-gray-600">
          <input
            type="checkbox"
            v-model="healthyOnly"
            @change="refreshPeers"
            class="rounded border-gray-300 text-primary-600 focus:ring-primary-500"
          />
          Show healthy only
        </label>
      </div>

      <DataTable
        :columns="peerColumns"
        :data="peers"
        :loading="loading"
        empty-message="No peers connected"
      >
        <template #cell-node_id="{ value }">
          <span class="font-mono text-sm">{{ truncate(value) }}</span>
        </template>
        <template #cell-latency_ms="{ value }">
          {{ value?.toFixed(1) || '-' }} ms
        </template>
        <template #cell-healthy="{ value }">
          <span
            :class="[
              'px-2 py-1 text-xs rounded-full',
              value ? 'bg-green-100 text-green-800' : 'bg-red-100 text-red-800'
            ]"
          >
            {{ value ? 'Healthy' : 'Unhealthy' }}
          </span>
        </template>
        <template #cell-success_rate="{ value }">
          <div class="flex items-center gap-2">
            <div class="flex-1 h-2 bg-gray-200 rounded-full overflow-hidden">
              <div
                class="h-full bg-green-500"
                :style="{ width: `${(value || 0) * 100}%` }"
              ></div>
            </div>
            <span class="text-sm text-gray-600">{{ ((value || 0) * 100).toFixed(0) }}%</span>
          </div>
        </template>
      </DataTable>

      <!-- Refresh button -->
      <div class="mt-4">
        <button @click="refreshPeers" class="btn btn-primary">
          Refresh Peers
        </button>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import MetricCard from '@/components/common/MetricCard.vue'
import DataTable from '@/components/common/DataTable.vue'

const store = useNodeStore()
const { peers, networkStats, loading } = storeToRefs(store)

const healthyOnly = ref(false)

const peerColumns = [
  { key: 'host', label: 'Host' },
  { key: 'port', label: 'Port' },
  { key: 'node_id', label: 'Node ID' },
  { key: 'latency_ms', label: 'Latency' },
  { key: 'healthy', label: 'Status' },
  { key: 'success_rate', label: 'Success Rate' }
]

const truncate = (str) => {
  if (!str || str.length < 16) return str
  return `${str.slice(0, 12)}...`
}

const refreshPeers = () => {
  store.fetchPeers(healthyOnly.value)
  store.fetchNetworkStats()
}

onMounted(() => {
  store.fetchPeers()
  store.fetchNetworkStats()
})
</script>
