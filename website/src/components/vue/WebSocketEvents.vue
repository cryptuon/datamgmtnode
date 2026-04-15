<script setup>
import { ref, onMounted, onUnmounted, computed } from 'vue';

const props = defineProps({
  wsUrl: {
    type: String,
    default: ''
  },
  maxEvents: {
    type: Number,
    default: 20
  }
});

// Compute WebSocket URL dynamically based on current host
const getWsUrl = () => {
  if (props.wsUrl) return props.wsUrl;
  if (typeof window === 'undefined') return '';
  const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
  return `${protocol}//${window.location.host}/ws`;
};

const events = ref([]);
const connected = ref(false);
const connecting = ref(true);
const error = ref(null);
let ws = null;
let reconnectTimeout = null;
let demoInterval = null;

const statusText = computed(() => {
  if (connecting.value) return 'Connecting...';
  if (connected.value) return 'Connected';
  if (error.value) return 'Demo Mode';
  return 'Disconnected';
});

const statusColor = computed(() => {
  if (connected.value) return 'bg-green-500';
  if (connecting.value) return 'bg-yellow-500';
  return 'bg-gray-400';
});

// Demo events when WebSocket is unavailable
const demoEventTypes = [
  { type: 'peer_joined', icon: '🟢', message: 'New peer connected' },
  { type: 'peer_left', icon: '🔴', message: 'Peer disconnected' },
  { type: 'data_shared', icon: '📤', message: 'Data shared to peer' },
  { type: 'data_received', icon: '📥', message: 'Data received from peer' },
  { type: 'compliance_recorded', icon: '⛓️', message: 'Event recorded on blockchain' },
  { type: 'payment_received', icon: '💰', message: 'Token payment received' },
];

function addEvent(event) {
  const timestamp = new Date().toLocaleTimeString();
  events.value.unshift({
    ...event,
    id: Date.now() + Math.random(),
    timestamp
  });

  // Keep only maxEvents
  if (events.value.length > props.maxEvents) {
    events.value = events.value.slice(0, props.maxEvents);
  }
}

function generateDemoEvent() {
  const eventType = demoEventTypes[Math.floor(Math.random() * demoEventTypes.length)];
  const peerId = `peer_${Math.random().toString(36).substring(2, 8)}`;

  addEvent({
    type: eventType.type,
    icon: eventType.icon,
    message: eventType.message,
    details: { peer_id: peerId }
  });
}

function connect() {
  connecting.value = true;
  error.value = null;

  const wsUrl = getWsUrl();
  if (!wsUrl) {
    error.value = 'WebSocket URL not available';
    connecting.value = false;
    startDemoMode();
    return;
  }

  try {
    ws = new WebSocket(wsUrl);

    ws.onopen = () => {
      connected.value = true;
      connecting.value = false;
      addEvent({
        type: 'system',
        icon: '✅',
        message: 'Connected to WebSocket',
        details: {}
      });
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        addEvent({
          type: data.type || 'unknown',
          icon: getEventIcon(data.type),
          message: data.message || data.type,
          details: data
        });
      } catch {
        // Handle non-JSON messages
        addEvent({
          type: 'message',
          icon: '💬',
          message: event.data,
          details: {}
        });
      }
    };

    ws.onclose = () => {
      connected.value = false;
      connecting.value = false;
      // Don't reconnect, switch to demo mode
      startDemoMode();
    };

    ws.onerror = () => {
      error.value = 'WebSocket unavailable';
      connected.value = false;
      connecting.value = false;
      ws.close();
      startDemoMode();
    };
  } catch {
    error.value = 'WebSocket unavailable';
    connecting.value = false;
    startDemoMode();
  }
}

function startDemoMode() {
  if (demoInterval) return;

  // Add initial demo event
  addEvent({
    type: 'system',
    icon: '🎮',
    message: 'Demo mode - simulated events',
    details: {}
  });

  // Generate demo events periodically
  demoInterval = setInterval(generateDemoEvent, 3000);
  // Generate a few initial events
  for (let i = 0; i < 3; i++) {
    setTimeout(generateDemoEvent, 500 * (i + 1));
  }
}

function getEventIcon(type) {
  const icons = {
    peer_joined: '🟢',
    peer_left: '🔴',
    data_shared: '📤',
    data_received: '📥',
    compliance_recorded: '⛓️',
    payment_received: '💰',
    payment_sent: '💸',
    health_check: '🩺',
    error: '❌',
    system: '⚙️'
  };
  return icons[type] || '📝';
}

function clearEvents() {
  events.value = [];
}

onMounted(() => {
  connect();
});

onUnmounted(() => {
  if (ws) {
    ws.close();
  }
  if (reconnectTimeout) {
    clearTimeout(reconnectTimeout);
  }
  if (demoInterval) {
    clearInterval(demoInterval);
  }
});
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 overflow-hidden">
    <div class="p-4 border-b border-gray-100 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <h3 class="font-semibold text-gray-900">Live Events</h3>
        <div class="flex items-center gap-2">
          <span
            :class="[statusColor, 'w-2 h-2 rounded-full', connecting ? 'animate-pulse' : '']"
          ></span>
          <span class="text-xs text-gray-500">{{ statusText }}</span>
        </div>
      </div>
      <button
        @click="clearEvents"
        class="text-xs text-gray-500 hover:text-gray-700"
      >
        Clear
      </button>
    </div>

    <div class="h-80 overflow-y-auto">
      <div v-if="events.length === 0" class="flex items-center justify-center h-full text-gray-500 text-sm">
        Waiting for events...
      </div>

      <div v-else class="divide-y divide-gray-50">
        <div
          v-for="event in events"
          :key="event.id"
          class="p-3 hover:bg-gray-50 transition-colors animate-fadeIn"
        >
          <div class="flex items-start gap-3">
            <span class="text-lg">{{ event.icon }}</span>
            <div class="flex-1 min-w-0">
              <div class="flex items-center justify-between gap-2">
                <span class="text-sm font-medium text-gray-900">{{ event.message }}</span>
                <span class="text-xs text-gray-400 whitespace-nowrap">{{ event.timestamp }}</span>
              </div>
              <div v-if="event.details.peer_id" class="text-xs text-gray-500 font-mono mt-1">
                {{ event.details.peer_id }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
@keyframes fadeIn {
  from {
    opacity: 0;
    transform: translateY(-10px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}

.animate-fadeIn {
  animation: fadeIn 0.3s ease-out;
}
</style>
