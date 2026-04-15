<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const props = defineProps({
  apiUrl: {
    type: String,
    default: '/api'
  },
  refreshInterval: {
    type: Number,
    default: 5000
  }
});

const status = ref(null);
const loading = ref(true);
const error = ref(null);
const lastUpdated = ref(null);
let intervalId = null;

const statusColor = computed(() => {
  if (!status.value) return 'bg-gray-400';
  if (status.value.healthy) return 'bg-green-500';
  return 'bg-red-500';
});

const statusText = computed(() => {
  if (loading.value) return 'Connecting...';
  if (error.value) return 'Offline';
  if (!status.value) return 'Unknown';
  return status.value.healthy ? 'Online' : 'Degraded';
});

async function fetchStatus() {
  try {
    const response = await fetch(`${props.apiUrl}/health`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    status.value = await response.json();
    error.value = null;
    lastUpdated.value = new Date();
  } catch (err) {
    error.value = err.message;
    status.value = null;
  } finally {
    loading.value = false;
  }
}

onMounted(() => {
  fetchStatus();
  intervalId = setInterval(fetchStatus, props.refreshInterval);
});

onUnmounted(() => {
  if (intervalId) {
    clearInterval(intervalId);
  }
});
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-900">Node Status</h3>
      <div class="flex items-center gap-2">
        <span
          :class="[statusColor, 'w-3 h-3 rounded-full', loading ? 'animate-pulse' : '']"
        ></span>
        <span class="text-sm font-medium" :class="error ? 'text-red-600' : 'text-gray-700'">
          {{ statusText }}
        </span>
      </div>
    </div>

    <div v-if="loading" class="space-y-3">
      <div class="h-4 bg-gray-200 rounded animate-pulse w-3/4"></div>
      <div class="h-4 bg-gray-200 rounded animate-pulse w-1/2"></div>
      <div class="h-4 bg-gray-200 rounded animate-pulse w-2/3"></div>
    </div>

    <div v-else-if="error" class="text-center py-4">
      <p class="text-red-600 text-sm">Unable to connect to demo node</p>
      <button
        @click="fetchStatus"
        class="mt-2 text-sm text-primary-600 hover:text-primary-700"
      >
        Retry
      </button>
    </div>

    <div v-else-if="status" class="space-y-3">
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Version</span>
        <span class="font-mono text-gray-900">{{ status.version || 'N/A' }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Network</span>
        <span class="font-mono text-gray-900">{{ status.network || 'sepolia' }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Peers</span>
        <span class="font-mono text-gray-900">{{ status.peers || 0 }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Uptime</span>
        <span class="font-mono text-gray-900">{{ status.uptime || 'N/A' }}</span>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-gray-600">Block Height</span>
        <span class="font-mono text-gray-900">{{ status.block_height?.toLocaleString() || 'N/A' }}</span>
      </div>
    </div>

    <div v-if="lastUpdated" class="mt-4 pt-4 border-t border-gray-100">
      <p class="text-xs text-gray-500 text-center">
        Last updated: {{ lastUpdated.toLocaleTimeString() }}
      </p>
    </div>
  </div>
</template>
