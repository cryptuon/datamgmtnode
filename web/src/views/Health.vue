<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Health Status</h1>

    <!-- Overview -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Overview</h2>
      <div class="space-y-4">
        <div class="flex items-center justify-between py-2 border-b">
          <span class="font-medium text-gray-600">Overall Status</span>
          <StatusBadge :status="health?.status || 'unknown'" />
        </div>
        <div class="flex items-center justify-between py-2 border-b">
          <span class="font-medium text-gray-600">Version</span>
          <span class="text-gray-900">{{ health?.version || 'Unknown' }}</span>
        </div>
        <div class="flex items-center justify-between py-2">
          <span class="font-medium text-gray-600">Node ID</span>
          <span class="text-gray-900 font-mono text-sm">{{ health?.node_id || 'Unknown' }}</span>
        </div>
      </div>
    </div>

    <!-- Components -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Components</h2>
      <div class="space-y-4">
        <div
          v-for="(status, name) in health?.components"
          :key="name"
          class="flex items-center justify-between py-3 px-4 bg-gray-50 rounded-lg"
        >
          <div>
            <span class="font-medium text-gray-900">{{ formatComponentName(name) }}</span>
            <p class="text-sm text-gray-500">{{ getComponentDescription(name) }}</p>
          </div>
          <StatusBadge :status="status" />
        </div>
      </div>
    </div>

    <!-- Refresh button -->
    <div class="mt-6">
      <button @click="refresh" class="btn btn-primary">
        Refresh Status
      </button>
    </div>
  </div>
</template>

<script setup>
import { onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import StatusBadge from '@/components/common/StatusBadge.vue'

const store = useNodeStore()
const { health } = storeToRefs(store)

const formatComponentName = (name) => {
  return name
    .split('_')
    .map(word => word.charAt(0).toUpperCase() + word.slice(1))
    .join(' ')
}

const getComponentDescription = (name) => {
  const descriptions = {
    blockchain: 'Connection to the EVM blockchain network',
    p2p_network: 'Peer-to-peer network for data distribution',
    encryption: 'Data encryption and key management'
  }
  return descriptions[name] || ''
}

const refresh = () => {
  store.fetchHealth()
}

onMounted(() => {
  store.fetchHealth()
})
</script>
