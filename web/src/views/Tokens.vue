<template>
  <div>
    <h1 class="text-2xl font-bold text-gray-900 mb-6">Tokens</h1>

    <!-- Token List -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Supported Tokens</h2>
      <DataTable
        :columns="tokenColumns"
        :data="tokens"
        :loading="loading"
        empty-message="No tokens configured"
      >
        <template #cell-address="{ value }">
          <span class="font-mono text-sm">
            {{ truncateAddress(value) }}
          </span>
        </template>
        <template #cell-type="{ value }">
          <span
            :class="[
              'px-2 py-1 text-xs rounded-full',
              value === 'native' ? 'bg-blue-100 text-blue-800' : 'bg-gray-100 text-gray-800'
            ]"
          >
            {{ value }}
          </span>
        </template>
      </DataTable>
    </div>

    <!-- Balance Check -->
    <div class="card mb-6">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Check Balance</h2>
      <div class="flex gap-4">
        <input
          v-model="balanceAddress"
          type="text"
          placeholder="Enter address (0x...)"
          class="form-input flex-1"
        />
        <button @click="checkBalance" class="btn btn-primary">
          Check Balance
        </button>
      </div>
      <div v-if="balanceResult" class="mt-4 p-4 bg-gray-50 rounded-lg">
        <div v-if="balanceResult.error" class="text-red-600">
          Error: {{ balanceResult.error }}
        </div>
        <div v-else>
          <div class="text-sm text-gray-500">Balance</div>
          <div class="text-2xl font-bold text-gray-900">{{ balanceResult.balance }}</div>
          <div class="text-sm text-gray-400 font-mono">{{ truncateAddress(balanceResult.token) }}</div>
        </div>
      </div>
    </div>

    <!-- Transfer Form -->
    <div class="card">
      <h2 class="text-lg font-semibold text-gray-900 mb-4">Transfer Tokens</h2>
      <form @submit.prevent="submitTransfer" class="space-y-4">
        <div>
          <label class="form-label">From Address</label>
          <input v-model="transferForm.from" type="text" class="form-input" placeholder="0x..." />
        </div>
        <div>
          <label class="form-label">To Address</label>
          <input v-model="transferForm.to" type="text" class="form-input" placeholder="0x..." />
        </div>
        <div>
          <label class="form-label">Amount (wei)</label>
          <input v-model="transferForm.amount" type="number" class="form-input" placeholder="1000000000000000000" />
        </div>
        <div>
          <label class="form-label">Token Address</label>
          <input v-model="transferForm.token" type="text" class="form-input" placeholder="0x... (leave empty for native)" />
        </div>
        <div class="flex gap-4">
          <button type="submit" class="btn btn-primary" :disabled="store.loading">
            {{ store.loading ? 'Processing...' : 'Transfer' }}
          </button>
          <button type="button" @click="clearTransferForm" class="btn btn-secondary">
            Clear
          </button>
        </div>
      </form>
      <div v-if="transferResult" class="mt-4 p-4 rounded-lg" :class="transferResult.success ? 'bg-green-50' : 'bg-red-50'">
        <div v-if="transferResult.success" class="text-green-800">
          Transfer successful! Tx: {{ truncateAddress(transferResult.tx_hash) }}
        </div>
        <div v-else class="text-red-800">
          Transfer failed: {{ transferResult.error }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import { storeToRefs } from 'pinia'
import { useNodeStore } from '@/stores/node'
import DataTable from '@/components/common/DataTable.vue'

const store = useNodeStore()
const { tokens, loading } = storeToRefs(store)

const balanceAddress = ref('')
const balanceResult = ref(null)

const transferForm = ref({
  from: '',
  to: '',
  amount: '',
  token: ''
})
const transferResult = ref(null)

const tokenColumns = [
  { key: 'address', label: 'Address' },
  { key: 'type', label: 'Type' },
  { key: 'symbol', label: 'Symbol' }
]

const truncateAddress = (addr) => {
  if (!addr || addr.length < 20) return addr
  return `${addr.slice(0, 10)}...${addr.slice(-8)}`
}

const checkBalance = async () => {
  if (!balanceAddress.value) return
  balanceResult.value = await store.getBalance(balanceAddress.value)
}

const submitTransfer = async () => {
  const { from, to, amount, token } = transferForm.value

  if (!from || !to || !amount) {
    transferResult.value = { error: 'All fields are required' }
    return
  }

  // Use native token if not specified
  let tokenAddr = token
  if (!tokenAddr && tokens.value.length > 0) {
    const native = tokens.value.find(t => t.type === 'native')
    if (native) tokenAddr = native.address
  }

  try {
    transferResult.value = await store.transfer(from, to, parseInt(amount), tokenAddr)
  } catch (e) {
    transferResult.value = { error: e.message }
  }
}

const clearTransferForm = () => {
  transferForm.value = { from: '', to: '', amount: '', token: '' }
  transferResult.value = null
}

onMounted(() => {
  store.fetchTokens()
})
</script>
