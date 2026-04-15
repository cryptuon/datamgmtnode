<script setup>
import { ref, onMounted, onUnmounted, watch } from 'vue';

const props = defineProps({
  apiUrl: {
    type: String,
    default: '/api'
  }
});

const canvas = ref(null);
const peers = ref([]);
const loading = ref(true);
const error = ref(null);
let animationId = null;

// Node positions for visualization
const nodes = ref([]);
const edges = ref([]);

// Demo data when API is unavailable
const demoNodes = [
  { id: 'self', x: 200, y: 200, radius: 12, color: '#0ea5e9', label: 'Your Node' },
  { id: 'peer1', x: 100, y: 100, radius: 8, color: '#22c55e', label: 'Peer 1' },
  { id: 'peer2', x: 300, y: 80, radius: 8, color: '#22c55e', label: 'Peer 2' },
  { id: 'peer3', x: 350, y: 200, radius: 8, color: '#22c55e', label: 'Peer 3' },
  { id: 'peer4', x: 280, y: 320, radius: 8, color: '#22c55e', label: 'Peer 4' },
  { id: 'peer5', x: 100, y: 280, radius: 8, color: '#22c55e', label: 'Peer 5' },
  { id: 'peer6', x: 50, y: 180, radius: 8, color: '#f59e0b', label: 'Peer 6' },
];

const demoEdges = [
  { from: 'self', to: 'peer1' },
  { from: 'self', to: 'peer2' },
  { from: 'self', to: 'peer3' },
  { from: 'self', to: 'peer4' },
  { from: 'self', to: 'peer5' },
  { from: 'self', to: 'peer6' },
  { from: 'peer1', to: 'peer2' },
  { from: 'peer3', to: 'peer4' },
  { from: 'peer5', to: 'peer6' },
];

async function fetchPeers() {
  try {
    const response = await fetch(`${props.apiUrl}/network/peers`, {
      method: 'GET',
      headers: { 'Accept': 'application/json' }
    });

    if (!response.ok) throw new Error(`HTTP ${response.status}`);

    const data = await response.json();
    peers.value = data.peers || [];
    generateNodesFromPeers();
  } catch (err) {
    error.value = 'Using demo visualization';
    // Use demo data
    nodes.value = demoNodes;
    edges.value = demoEdges;
  } finally {
    loading.value = false;
  }
}

function generateNodesFromPeers() {
  const centerX = 200;
  const centerY = 200;
  const radius = 150;

  // Self node at center
  nodes.value = [
    { id: 'self', x: centerX, y: centerY, radius: 12, color: '#0ea5e9', label: 'Your Node' }
  ];

  // Position peers in a circle
  peers.value.forEach((peer, index) => {
    const angle = (2 * Math.PI * index) / peers.value.length;
    nodes.value.push({
      id: peer.node_id || `peer${index}`,
      x: centerX + radius * Math.cos(angle),
      y: centerY + radius * Math.sin(angle),
      radius: 8,
      color: peer.health === 'healthy' ? '#22c55e' : '#f59e0b',
      label: `Peer ${index + 1}`
    });
  });

  // Create edges from self to all peers
  edges.value = nodes.value.slice(1).map(node => ({
    from: 'self',
    to: node.id
  }));
}

function draw() {
  if (!canvas.value) return;

  const ctx = canvas.value.getContext('2d');
  const width = canvas.value.width;
  const height = canvas.value.height;

  // Clear canvas
  ctx.fillStyle = '#f9fafb';
  ctx.fillRect(0, 0, width, height);

  // Draw edges
  ctx.strokeStyle = '#d1d5db';
  ctx.lineWidth = 1;
  edges.value.forEach(edge => {
    const from = nodes.value.find(n => n.id === edge.from);
    const to = nodes.value.find(n => n.id === edge.to);
    if (from && to) {
      ctx.beginPath();
      ctx.moveTo(from.x, from.y);
      ctx.lineTo(to.x, to.y);
      ctx.stroke();
    }
  });

  // Draw nodes
  nodes.value.forEach(node => {
    // Glow effect for main node
    if (node.id === 'self') {
      ctx.beginPath();
      const gradient = ctx.createRadialGradient(node.x, node.y, 0, node.x, node.y, node.radius * 2);
      gradient.addColorStop(0, 'rgba(14, 165, 233, 0.3)');
      gradient.addColorStop(1, 'rgba(14, 165, 233, 0)');
      ctx.fillStyle = gradient;
      ctx.arc(node.x, node.y, node.radius * 2, 0, 2 * Math.PI);
      ctx.fill();
    }

    // Node circle
    ctx.beginPath();
    ctx.fillStyle = node.color;
    ctx.arc(node.x, node.y, node.radius, 0, 2 * Math.PI);
    ctx.fill();

    // Node border
    ctx.strokeStyle = '#ffffff';
    ctx.lineWidth = 2;
    ctx.stroke();
  });

  // Draw labels
  ctx.fillStyle = '#374151';
  ctx.font = '10px system-ui';
  ctx.textAlign = 'center';
  nodes.value.forEach(node => {
    ctx.fillText(node.label, node.x, node.y + node.radius + 14);
  });
}

function animate() {
  // Add slight movement to peer nodes
  nodes.value.forEach((node, index) => {
    if (node.id !== 'self') {
      node.x += Math.sin(Date.now() / 1000 + index) * 0.2;
      node.y += Math.cos(Date.now() / 1000 + index * 0.7) * 0.2;
    }
  });
  draw();
  animationId = requestAnimationFrame(animate);
}

onMounted(() => {
  fetchPeers();
  // Start animation after a short delay
  setTimeout(() => {
    if (nodes.value.length > 0) {
      animate();
    }
  }, 500);
});

onUnmounted(() => {
  if (animationId) {
    cancelAnimationFrame(animationId);
  }
});

watch(nodes, () => {
  if (!animationId && nodes.value.length > 0) {
    animate();
  }
}, { deep: true });
</script>

<template>
  <div class="bg-white rounded-xl shadow-sm border border-gray-100 p-6">
    <div class="flex items-center justify-between mb-4">
      <h3 class="font-semibold text-gray-900">P2P Network</h3>
      <span class="text-xs text-gray-500">{{ nodes.length }} nodes</span>
    </div>

    <div v-if="loading" class="flex items-center justify-center h-64">
      <div class="text-gray-500">Connecting to network...</div>
    </div>

    <div v-else class="relative">
      <canvas
        ref="canvas"
        width="400"
        height="400"
        class="w-full h-auto rounded-lg"
      ></canvas>

      <div v-if="error" class="absolute top-2 right-2 px-2 py-1 bg-yellow-100 text-yellow-800 text-xs rounded">
        {{ error }}
      </div>
    </div>

    <div class="mt-4 flex items-center justify-center gap-6 text-xs">
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-primary-500"></span>
        <span class="text-gray-600">Your Node</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-green-500"></span>
        <span class="text-gray-600">Healthy Peer</span>
      </div>
      <div class="flex items-center gap-2">
        <span class="w-3 h-3 rounded-full bg-yellow-500"></span>
        <span class="text-gray-600">Degraded</span>
      </div>
    </div>
  </div>
</template>
