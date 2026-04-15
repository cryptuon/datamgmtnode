<script setup>
import { ref, computed } from 'vue';

const props = defineProps({
  apiUrl: {
    type: String,
    default: '/api'
  }
});

const address = ref('');
const balances = ref(null);
const loading = ref(false);
const error = ref(null);

const isValidAddress = computed(() => {
  return /^0x[a-fA-F0-9]{40}$/.test(address.value);
});

const sampleAddresses = [
  { label: 'Demo Wallet', address: '0x742d35Cc6634C0532925a3b844Bc9e7595f8fE21' },
  { label: 'Test Account', address: '0xAb5801a7D398351b8bE11C439e05C5B3259aeC9B' }
];

async function checkBalance() {
  if (!isValidAddress.value) {
    error.value = 'Please enter a valid Ethereum address';
    return;
  }

  loading.value = true;
  error.value = null;
  balances.value = null;

  try {
    const response = await fetch(`${props.apiUrl}/balance/${address.value}`, {
      method: 'GET',
      headers: {
        'Accept': 'application/json'
      }
    });

    if (!response.ok) {
      throw new Error(`HTTP ${response.status}`);
    }

    balances.value = await response.json();
  } catch (err) {
    error.value = 'Unable to fetch balance. Demo node may be offline.';
    // Provide mock data for demo purposes
    balances.value = {
      native: { symbol: 'ETH', balance: '0.0', formatted: '0.0 ETH' },
      tokens: [
        { symbol: 'USDC', balance: '0.0', formatted: '0.00 USDC' },
        { symbol: 'USDT', balance: '0.0', formatted: '0.00 USDT' }
      ]
    };
  } finally {
    loading.value = false;
  }
}

function useAddress(addr) {
  address.value = addr;
  checkBalance();
}

function formatBalance(balance, decimals = 18) {
  const num = parseFloat(balance) / Math.pow(10, decimals);
  return num.toLocaleString(undefined, { maximumFractionDigits: 4 });
}
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <h3 class="font-semibold text-gray-900 mb-4">Token Balance Checker</h3>

    <div class="space-y-4">
      <div>
        <label for="address" class="block text-sm font-medium text-gray-700 mb-1">
          Wallet Address
        </label>
        <div class="flex gap-2">
          <input
            id="address"
            v-model="address"
            type="text"
            placeholder="0x..."
            class="flex-1 px-3 py-2 border border-gray-300 rounded-lg text-sm font-mono focus:ring-2 focus:ring-primary-500 focus:border-primary-500"
            :class="{ 'border-red-300': address && !isValidAddress }"
          />
          <button
            @click="checkBalance"
            :disabled="loading || !isValidAddress"
            class="px-4 py-2 bg-primary-600 text-white text-sm font-medium rounded-lg hover:bg-primary-700 disabled:opacity-50 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading">...</span>
            <span v-else>Check</span>
          </button>
        </div>
        <p v-if="address && !isValidAddress" class="mt-1 text-xs text-red-600">
          Invalid Ethereum address format
        </p>
      </div>

      <div class="flex flex-wrap gap-2">
        <span class="text-xs text-gray-500">Try:</span>
        <button
          v-for="sample in sampleAddresses"
          :key="sample.address"
          @click="useAddress(sample.address)"
          class="text-xs text-primary-600 hover:text-primary-700 hover:underline"
        >
          {{ sample.label }}
        </button>
      </div>

      <div v-if="error" class="p-3 bg-yellow-50 border border-yellow-200 rounded-lg">
        <p class="text-sm text-yellow-800">{{ error }}</p>
      </div>

      <div v-if="balances" class="space-y-3 pt-4 border-t border-gray-100">
        <div v-if="balances.native" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <div class="flex items-center gap-2">
            <span class="w-8 h-8 bg-purple-100 rounded-full flex items-center justify-center text-xs font-bold text-purple-600">
              {{ balances.native.symbol?.charAt(0) || 'E' }}
            </span>
            <span class="font-medium text-gray-900">{{ balances.native.symbol || 'ETH' }}</span>
          </div>
          <span class="font-mono text-gray-900">{{ balances.native.formatted || balances.native.balance }}</span>
        </div>

        <div v-for="token in balances.tokens" :key="token.symbol" class="flex justify-between items-center p-3 bg-gray-50 rounded-lg">
          <div class="flex items-center gap-2">
            <span class="w-8 h-8 bg-blue-100 rounded-full flex items-center justify-center text-xs font-bold text-blue-600">
              {{ token.symbol?.charAt(0) || 'T' }}
            </span>
            <span class="font-medium text-gray-900">{{ token.symbol }}</span>
          </div>
          <span class="font-mono text-gray-900">{{ token.formatted || token.balance }}</span>
        </div>

        <p class="text-xs text-gray-500 text-center pt-2">
          Balances on Sepolia testnet
        </p>
      </div>
    </div>
  </div>
</template>
