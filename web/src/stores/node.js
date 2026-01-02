import { defineStore } from 'pinia'
import { ref, computed } from 'vue'

export const useNodeStore = defineStore('node', () => {
  // State
  const health = ref(null)
  const tokens = ref([])
  const peers = ref([])
  const networkStats = ref(null)
  const complianceHistory = ref([])
  const loading = ref(false)
  const error = ref(null)

  // Getters
  const isHealthy = computed(() => health.value?.status === 'healthy')
  const healthyPeerCount = computed(() =>
    peers.value.filter(p => p.healthy).length
  )
  const totalPeerCount = computed(() => peers.value.length)

  // Actions
  async function fetchHealth() {
    try {
      const response = await fetch('/api/health')
      health.value = await response.json()
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchTokens() {
    try {
      const response = await fetch('/api/tokens')
      const data = await response.json()
      tokens.value = data.tokens || []
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchNetworkStats() {
    try {
      const response = await fetch('/api/network/stats')
      networkStats.value = await response.json()
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchPeers(healthyOnly = false) {
    try {
      const url = healthyOnly ? '/api/network/peers?healthy=true' : '/api/network/peers'
      const response = await fetch(url)
      const data = await response.json()
      peers.value = data.peers || []
    } catch (e) {
      error.value = e.message
    }
  }

  async function fetchComplianceHistory(filters = null) {
    try {
      let url = '/api/compliance_history'
      if (filters && filters.length > 0) {
        url += `?filters=${filters.join(',')}`
      }
      const response = await fetch(url)
      const data = await response.json()
      complianceHistory.value = data.history || []
    } catch (e) {
      error.value = e.message
    }
  }

  async function getBalance(address) {
    try {
      const response = await fetch(`/api/balance/${address}`)
      return await response.json()
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function transfer(from, to, amount, token) {
    loading.value = true
    try {
      const response = await fetch('/api/transfer', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ from, to, amount, token })
      })
      return await response.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function shareData(data, recipient, paymentToken = null, paymentAmount = null) {
    loading.value = true
    try {
      const body = { data, recipient }
      if (paymentToken) {
        body.payment_token = paymentToken
        body.payment_amount = paymentAmount
      }
      const response = await fetch('/api/share_data', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body)
      })
      return await response.json()
    } catch (e) {
      error.value = e.message
      throw e
    } finally {
      loading.value = false
    }
  }

  async function getData(dataHash) {
    try {
      const response = await fetch(`/api/data/${dataHash}`)
      return await response.json()
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  async function verifyData(dataHash) {
    try {
      const response = await fetch(`/api/verify_data/${dataHash}`)
      return await response.json()
    } catch (e) {
      error.value = e.message
      return null
    }
  }

  // Handle WebSocket events
  function handleEvent(event) {
    switch (event.type) {
      case 'health.update':
        health.value = event.data
        break
      case 'network.stats_update':
        networkStats.value = event.data
        break
      case 'network.peer_connected':
      case 'network.peer_disconnected':
        fetchPeers()
        break
      case 'token.transfer_completed':
      case 'token.balance_update':
        fetchTokens()
        break
      case 'token.added':
        fetchTokens()
        break
      case 'compliance.event':
        complianceHistory.value.unshift(event.data)
        break
      case 'data.shared':
      case 'data.received':
        // Could trigger UI notification
        break
    }
  }

  return {
    // State
    health,
    tokens,
    peers,
    networkStats,
    complianceHistory,
    loading,
    error,
    // Getters
    isHealthy,
    healthyPeerCount,
    totalPeerCount,
    // Actions
    fetchHealth,
    fetchTokens,
    fetchNetworkStats,
    fetchPeers,
    fetchComplianceHistory,
    getBalance,
    transfer,
    shareData,
    getData,
    verifyData,
    handleEvent
  }
})
