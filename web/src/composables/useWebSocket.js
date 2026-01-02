import { ref, onMounted, onUnmounted } from 'vue'

/**
 * WebSocket composable for real-time updates
 */
export function useWebSocket() {
  const connected = ref(false)
  const events = ref([])
  let ws = null
  let reconnectTimer = null
  let reconnectAttempts = 0
  const maxReconnectAttempts = 10

  const connect = () => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const wsUrl = `${protocol}//${window.location.host}/ws`

    try {
      ws = new WebSocket(wsUrl)

      ws.onopen = () => {
        connected.value = true
        reconnectAttempts = 0
        console.log('WebSocket connected')
      }

      ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          events.value.push(data)

          // Keep only last 100 events
          if (events.value.length > 100) {
            events.value.shift()
          }
        } catch (e) {
          console.error('Failed to parse WebSocket message:', e)
        }
      }

      ws.onclose = () => {
        connected.value = false
        console.log('WebSocket disconnected')

        // Attempt reconnection with exponential backoff
        if (reconnectAttempts < maxReconnectAttempts) {
          const delay = Math.min(1000 * Math.pow(2, reconnectAttempts), 30000)
          reconnectAttempts++
          console.log(`Reconnecting in ${delay}ms (attempt ${reconnectAttempts})...`)
          reconnectTimer = setTimeout(connect, delay)
        }
      }

      ws.onerror = (error) => {
        console.error('WebSocket error:', error)
      }
    } catch (e) {
      console.error('Failed to create WebSocket:', e)
    }
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws) {
      ws.close()
      ws = null
    }
  }

  const send = (message) => {
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message))
    }
  }

  const ping = () => {
    send({ type: 'ping' })
  }

  const getEventsByType = (type) => {
    return events.value.filter(e => e.type === type || e.type.startsWith(type + '.'))
  }

  const clearEvents = () => {
    events.value = []
  }

  onMounted(connect)
  onUnmounted(disconnect)

  return {
    connected,
    events,
    send,
    ping,
    getEventsByType,
    clearEvents,
    disconnect,
    reconnect: connect
  }
}
