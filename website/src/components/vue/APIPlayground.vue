<script setup>
import { ref, computed, watch } from 'vue';

const props = defineProps({
  apiUrl: {
    type: String,
    default: '/api'
  }
});

const endpoints = [
  { method: 'GET', path: '/health', description: 'Check node health status', params: [] },
  { method: 'GET', path: '/network/stats', description: 'Get P2P network statistics', params: [] },
  { method: 'GET', path: '/network/peers', description: 'List connected peers', params: [] },
  { method: 'GET', path: '/tokens', description: 'List supported tokens', params: [] },
  { method: 'GET', path: '/balance/{address}', description: 'Get token balance', params: ['address'] },
  { method: 'GET', path: '/verify_data/{hash}', description: 'Verify data on blockchain', params: ['hash'] },
];

const selectedEndpoint = ref(endpoints[0]);
const paramValues = ref({});
const response = ref(null);
const loading = ref(false);
const error = ref(null);
const requestTime = ref(null);

const resolvedPath = computed(() => {
  let path = selectedEndpoint.value.path;
  for (const param of selectedEndpoint.value.params) {
    const value = paramValues.value[param] || `{${param}}`;
    path = path.replace(`{${param}}`, value);
  }
  return path;
});

const fullUrl = computed(() => {
  return `${props.apiUrl}${resolvedPath.value}`;
});

const curlCommand = computed(() => {
  return `curl -X ${selectedEndpoint.value.method} "${fullUrl.value}"`;
});

watch(selectedEndpoint, () => {
  paramValues.value = {};
  response.value = null;
  error.value = null;
});

async function sendRequest() {
  // Validate params
  for (const param of selectedEndpoint.value.params) {
    if (!paramValues.value[param]) {
      error.value = `Please provide a value for ${param}`;
      return;
    }
  }

  loading.value = true;
  error.value = null;
  response.value = null;
  const startTime = performance.now();

  try {
    const res = await fetch(fullUrl.value, {
      method: selectedEndpoint.value.method,
      headers: {
        'Accept': 'application/json'
      }
    });

    requestTime.value = Math.round(performance.now() - startTime);

    if (!res.ok) {
      throw new Error(`HTTP ${res.status}: ${res.statusText}`);
    }

    response.value = await res.json();
  } catch (err) {
    error.value = err.message;
    requestTime.value = Math.round(performance.now() - startTime);
    // Provide mock response for demo
    if (selectedEndpoint.value.path === '/health') {
      response.value = {
        status: 'demo',
        message: 'Demo mode - actual node offline',
        healthy: true,
        version: '1.0.0',
        network: 'sepolia'
      };
    }
  } finally {
    loading.value = false;
  }
}

function copyToClipboard(text) {
  navigator.clipboard.writeText(text);
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-6 border-b border-gray-100">
      <h3 class="font-semibold text-gray-900 mb-4">API Playground</h3>

      <div class="space-y-4">
        <!-- Endpoint Selector -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Endpoint</label>
          <div class="grid gap-2">
            <button
              v-for="endpoint in endpoints"
              :key="endpoint.path"
              @click="selectedEndpoint = endpoint"
              class="flex items-center gap-3 p-3 text-left rounded-lg border transition-colors"
              :class="selectedEndpoint === endpoint ? 'border-primary-500 bg-primary-50' : 'border-gray-200 hover:border-gray-300'"
            >
              <span
                class="px-2 py-1 text-xs font-mono rounded"
                :class="endpoint.method === 'GET' ? 'bg-green-100 text-green-700' : 'bg-blue-100 text-blue-700'"
              >
                {{ endpoint.method }}
              </span>
              <div class="flex-1 min-w-0">
                <div class="font-mono text-sm text-gray-900 truncate">{{ endpoint.path }}</div>
                <div class="text-xs text-gray-500">{{ endpoint.description }}</div>
              </div>
            </button>
          </div>
        </div>

        <!-- Parameters -->
        <div v-if="selectedEndpoint.params.length > 0" class="space-y-3">
          <label class="block text-sm font-medium text-gray-700">Parameters</label>
          <div v-for="param in selectedEndpoint.params" :key="param" class="flex items-center gap-2">
            <span class="text-sm text-gray-600 w-20">{{ param }}:</span>
            <input
              v-model="paramValues[param]"
              type="text"
              :placeholder="`Enter ${param}`"
              class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            />
          </div>
        </div>

        <!-- Request URL -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-2">Request URL</label>
          <div class="flex items-center gap-2 p-3 bg-gray-100 rounded-lg font-mono text-sm">
            <span class="text-green-600">{{ selectedEndpoint.method }}</span>
            <span class="text-gray-700 flex-1 truncate">{{ fullUrl }}</span>
          </div>
        </div>

        <!-- Send Button -->
        <button
          @click="sendRequest"
          :disabled="loading"
          class="w-full px-4 py-3 bg-primary-600 text-white font-semibold rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
        >
          <span v-if="loading">Sending...</span>
          <span v-else>Send Request</span>
        </button>
      </div>
    </div>

    <!-- Response -->
    <div class="p-6 bg-gray-900">
      <div class="flex items-center justify-between mb-3">
        <span class="text-sm text-gray-400">Response</span>
        <div class="flex items-center gap-3">
          <span v-if="requestTime !== null" class="text-xs text-gray-500">
            {{ requestTime }}ms
          </span>
          <button
            v-if="response"
            @click="copyToClipboard(JSON.stringify(response, null, 2))"
            class="text-xs text-gray-400 hover:text-white transition-colors"
          >
            Copy
          </button>
        </div>
      </div>

      <div v-if="loading" class="text-gray-500 text-sm">
        Loading...
      </div>

      <div v-else-if="error && !response" class="text-red-400 text-sm font-mono">
        Error: {{ error }}
      </div>

      <pre v-else-if="response" class="text-green-400 text-sm font-mono overflow-x-auto whitespace-pre-wrap">{{ JSON.stringify(response, null, 2) }}</pre>

      <div v-else class="text-gray-500 text-sm">
        Click "Send Request" to see the response
      </div>
    </div>

    <!-- cURL -->
    <div class="p-4 bg-gray-800 border-t border-gray-700">
      <div class="flex items-center justify-between mb-2">
        <span class="text-xs text-gray-400">cURL</span>
        <button
          @click="copyToClipboard(curlCommand)"
          class="text-xs text-gray-400 hover:text-white transition-colors"
        >
          Copy
        </button>
      </div>
      <code class="text-xs text-gray-300 font-mono break-all">{{ curlCommand }}</code>
    </div>
  </div>
</template>
