<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Data Sharing</h1>

    <!-- Share Data Form -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Share Data</h2>
      <form @submit.prevent="submitShare" class="space-y-4">
        <div>
          <label class="form-label">Recipient Address</label>
          <input v-model="shareForm.recipient" type="text" class="form-input" placeholder="0x..." />
        </div>
        <div>
          <label class="form-label">Data</label>
          <textarea
            v-model="shareForm.data"
            rows="4"
            class="form-input"
            placeholder="Enter data to share..."
          ></textarea>
        </div>
        <div class="flex gap-4">
          <button type="submit" class="btn btn-primary" :disabled="store.loading">
            {{ store.loading ? 'Sharing...' : 'Share Data' }}
          </button>
          <button type="button" @click="clearShareForm" class="btn btn-secondary">
            Clear
          </button>
        </div>
      </form>
      <div v-if="shareResult" class="mt-4 p-4 rounded-lg" :class="shareResult.success ? 'bg-green-50' : 'bg-red-50'">
        <div v-if="shareResult.success" class="text-green-800">
          Data shared successfully!<br />
          Tx: <span class="font-mono">{{ truncate(shareResult.tx_hash) }}</span>
        </div>
        <div v-else class="text-red-800">
          Failed: {{ shareResult.error }}
        </div>
      </div>
    </div>

    <!-- Retrieve Data -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Retrieve Data</h2>
      <div class="flex gap-4 mb-4">
        <input
          v-model="dataHash"
          type="text"
          placeholder="Enter 64-character data hash"
          class="form-input flex-1"
        />
        <button @click="retrieveData" class="btn btn-primary">
          Retrieve
        </button>
      </div>
      <div v-if="retrieveResult" class="p-4 bg-gray-50 rounded-lg">
        <div v-if="retrieveResult.error" class="text-red-600">
          Error: {{ retrieveResult.error }}
        </div>
        <div v-else>
          <div class="text-sm text-gray-500 mb-2">Data Found</div>
          <div class="bg-white p-3 rounded border font-mono text-sm overflow-x-auto">
            {{ retrieveResult.data }}
          </div>
        </div>
      </div>
    </div>

    <!-- Verify Data -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Verify Compliance</h2>
      <div class="flex gap-4 mb-4">
        <input
          v-model="verifyHash"
          type="text"
          placeholder="Enter 64-character data hash"
          class="form-input flex-1"
        />
        <button @click="verifyData" class="btn btn-primary">
          Verify
        </button>
      </div>
      <div v-if="verifyResult" class="p-4 rounded-lg" :class="verifyResult.verified ? 'bg-green-50' : 'bg-yellow-50'">
        <div v-if="verifyResult.error" class="text-red-600">
          Error: {{ verifyResult.error }}
        </div>
        <div v-else>
          <div class="flex items-center gap-2">
            <span v-if="verifyResult.verified" class="text-green-600 font-medium">Verified</span>
            <span v-else class="text-yellow-600 font-medium">Not Verified</span>
          </div>
          <div class="text-sm text-gray-500 mt-1">
            Event Type: {{ verifyResult.event_type }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref } from 'vue'
import { useNodeStore } from '@/stores/node'

const store = useNodeStore()

const shareForm = ref({
  recipient: '',
  data: ''
})
const shareResult = ref(null)

const dataHash = ref('')
const retrieveResult = ref(null)

const verifyHash = ref('')
const verifyResult = ref(null)

const truncate = (str) => {
  if (!str || str.length < 30) return str
  return `${str.slice(0, 20)}...${str.slice(-10)}`
}

const submitShare = async () => {
  const { recipient, data } = shareForm.value

  if (!recipient || !data) {
    shareResult.value = { error: 'Recipient and data are required' }
    return
  }

  try {
    shareResult.value = await store.shareData(data, recipient)
  } catch (e) {
    shareResult.value = { error: e.message }
  }
}

const clearShareForm = () => {
  shareForm.value = { recipient: '', data: '' }
  shareResult.value = null
}

const retrieveData = async () => {
  if (!dataHash.value || dataHash.value.length !== 64) {
    retrieveResult.value = { error: 'Hash must be 64 characters' }
    return
  }

  retrieveResult.value = await store.getData(dataHash.value)
}

const verifyData = async () => {
  if (!verifyHash.value || verifyHash.value.length !== 64) {
    verifyResult.value = { error: 'Hash must be 64 characters' }
    return
  }

  verifyResult.value = await store.verifyData(verifyHash.value)
}
</script>
