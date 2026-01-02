<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Compliance History</h1>

    <!-- Filters -->
    <div class="card mb-6">
      <div class="flex gap-4">
        <input
          v-model="filterInput"
          type="text"
          placeholder="Filter by type (e.g., data_share)"
          class="form-input flex-1"
        />
        <button @click="applyFilter" class="btn btn-primary">
          Apply Filter
        </button>
        <button @click="clearFilter" class="btn btn-secondary">
          Clear
        </button>
      </div>
      <div v-if="activeFilters.length > 0" class="mt-3 flex gap-2">
        <span class="text-sm text-gray-500">Active filters:</span>
        <span
          v-for="filter in activeFilters"
          :key="filter"
          class="px-2 py-1 bg-primary-100 text-primary-800 text-xs rounded-full"
        >
          {{ filter }}
        </span>
      </div>
    </div>

    <!-- History Table -->
    <div class="card mb-6">
      <div class="flex justify-between items-center mb-4">
        <h2 class="text-lg font-semibold text-gray-900">Events</h2>
        <span class="text-sm text-gray-500">{{ complianceHistory.length }} events</span>
      </div>
      <DataTable
        :columns="columns"
        :data="complianceHistory"
        :loading="loading"
        empty-message="No compliance events found"
      >
        <template #cell-type="{ value }">
          <span class="px-2 py-1 bg-gray-100 text-gray-800 text-xs rounded-full">
            {{ value }}
          </span>
        </template>
        <template #cell-hash="{ value }">
          <span class="font-mono text-sm">{{ truncate(value) }}</span>
        </template>
        <template #cell-tx_hash="{ value }">
          <span class="font-mono text-sm">{{ truncate(value) }}</span>
        </template>
        <template #cell-timestamp="{ value }">
          {{ formatTime(value) }}
        </template>
      </DataTable>
    </div>

    <!-- Statistics -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Statistics</h2>
      <div class="grid grid-cols-2 gap-4">
        <div class="p-4 bg-gray-50 rounded-lg">
          <div class="text-sm text-gray-500">Total Events</div>
          <div class="text-2xl font-bold text-gray-900">{{ complianceHistory.length }}</div>
        </div>
        <div class="p-4 bg-gray-50 rounded-lg">
          <div class="text-sm text-gray-500">Event Types</div>
          <div class="text-2xl font-bold text-gray-900">{{ uniqueTypes.length }}</div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, computed, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import DataTable from '@/components/common/DataTable.vue'

const store = useNodeStore()
const { complianceHistory, loading } = storeToRefs(store)

const filterInput = ref('')
const activeFilters = ref([])

const columns = [
  { key: 'type', label: 'Type' },
  { key: 'hash', label: 'Hash' },
  { key: 'block', label: 'Block' },
  { key: 'tx_hash', label: 'Tx Hash' },
  { key: 'timestamp', label: 'Time' }
]

const uniqueTypes = computed(() => {
  const types = new Set(complianceHistory.value.map(e => e.type))
  return Array.from(types)
})

const truncate = (str) => {
  if (!str || str.length < 20) return str
  return `${str.slice(0, 8)}...${str.slice(-6)}`
}

const formatTime = (timestamp) => {
  if (!timestamp) return '-'
  return new Date(timestamp * 1000).toLocaleString()
}

const applyFilter = () => {
  if (filterInput.value) {
    activeFilters.value = filterInput.value.split(',').map(f => f.trim())
    store.fetchComplianceHistory(activeFilters.value)
  }
}

const clearFilter = () => {
  filterInput.value = ''
  activeFilters.value = []
  store.fetchComplianceHistory()
}

onMounted(() => {
  store.fetchComplianceHistory()
})
</script>
