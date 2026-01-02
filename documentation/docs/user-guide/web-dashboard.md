# Web Dashboard

The DataMgmt Node includes a web-based dashboard built with Vue.js for monitoring and managing your node through a browser interface.

## Overview

The web dashboard provides:

- **Real-time updates** via WebSocket connection
- **Node health monitoring** with component status
- **Token management** including balances and transfers
- **Data sharing** interface for encrypted data operations
- **Compliance tracking** with event history
- **Network visualization** of connected peers

## Building the Dashboard

The dashboard must be built before use. This compiles the Vue.js application and copies it to the node's static directory.

### Prerequisites

- Node.js 18+ and npm

### Build Steps

```bash
# Build the dashboard
python scripts/build_dashboard.py
```

This will:

1. Install npm dependencies
2. Build the Vue.js application with Vite
3. Copy the output to `datamgmtnode/dashboard/static/`

## Accessing the Dashboard

Once built, the dashboard is served automatically when the node starts:

```bash
# Start the node
poetry run python -m datamgmtnode.main

# Dashboard available at:
# http://localhost:8082
```

## Pages

### Dashboard (Home)

The main dashboard provides an overview of:

- Node status and health indicators
- Recent activity and events
- Quick access to common operations

**Route:** `/`

### Health

Detailed health status of all node components:

| Component | Description |
|-----------|-------------|
| **Blockchain** | Ethereum/EVM connection status |
| **P2P Network** | Kademlia DHT network status |
| **Encryption** | Key manager initialization status |

**Route:** `/health`

### Tokens

Token management interface:

- View token balances for any address
- Initiate token transfers
- Add new ERC-20 tokens to the supported list

**Route:** `/tokens`

### Data Sharing

Data sharing operations:

- Share encrypted data with recipients
- Retrieve shared data by hash
- Verify data compliance status

**Route:** `/data`

### Compliance

Compliance event history and verification:

- View all recorded compliance events
- Filter by event type
- Verify specific data hashes

**Route:** `/compliance`

### Network

P2P network information:

- Connected peer list
- Network statistics
- Peer health status

**Route:** `/network`

## Real-Time Updates

The dashboard maintains a WebSocket connection for real-time updates:

```
ws://localhost:8082/ws
```

### Event Types

| Event | Description |
|-------|-------------|
| `health.update` | Node health status change |
| `health.component_change` | Individual component status change |
| `token.balance_update` | Token balance changed |
| `token.transfer_completed` | Transfer succeeded |
| `token.transfer_failed` | Transfer failed |
| `data.shared` | Data was shared |
| `data.received` | Data was received |
| `data.verified` | Data compliance verified |
| `compliance.event` | Compliance event recorded |
| `network.peer_connected` | New peer connected |
| `network.peer_disconnected` | Peer disconnected |
| `network.stats_update` | Network statistics updated |
| `system.error` | System error occurred |

### WebSocket Messages

**Ping/Pong:**

```json
// Send
{"type": "ping"}

// Receive
{"type": "pong"}
```

**Request Event History:**

```json
// Send
{"type": "get_history", "count": 50}

// Receive
{
  "type": "history",
  "data": {
    "events": [...],
    "count": 50
  }
}
```

## Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Vue 3 (Composition API) |
| **Build Tool** | Vite 5 |
| **Styling** | Tailwind CSS 3 |
| **State Management** | Pinia |
| **Routing** | Vue Router 4 |
| **Utilities** | VueUse |

### Project Structure

```
web/
├── src/
│   ├── main.js              # Application entry point
│   ├── App.vue              # Root component
│   ├── router/
│   │   └── index.js         # Route definitions
│   ├── stores/
│   │   └── node.js          # Pinia state store
│   ├── composables/
│   │   ├── useApi.js        # API client composable
│   │   └── useWebSocket.js  # WebSocket composable
│   ├── components/
│   │   ├── layout/
│   │   │   ├── Navbar.vue   # Navigation bar
│   │   │   └── Sidebar.vue  # Side navigation
│   │   └── common/
│   │       ├── MetricCard.vue   # Metric display card
│   │       ├── StatusBadge.vue  # Status indicator
│   │       └── DataTable.vue    # Data table component
│   └── views/
│       ├── Dashboard.vue    # Home dashboard
│       ├── Health.vue       # Health status
│       ├── Tokens.vue       # Token management
│       ├── DataSharing.vue  # Data operations
│       ├── Compliance.vue   # Compliance history
│       └── Network.vue      # Network info
├── index.html
├── package.json
├── vite.config.js
├── tailwind.config.js
└── postcss.config.js
```

### Composables

**useWebSocket:**

```javascript
import { useWebSocket } from '@/composables/useWebSocket'

const { connected, events, send, getEventsByType } = useWebSocket()

// Check connection status
if (connected.value) {
  // Send custom message
  send({ type: 'get_history', count: 100 })
}

// Get events by type
const tokenEvents = getEventsByType('token')
```

**useApi:**

```javascript
import { useApi } from '@/composables/useApi'

const { get, post, loading, error } = useApi()

// Fetch health status
const health = await get('/api/health')

// Transfer tokens
const result = await post('/api/transfer', {
  from_address: '0x...',
  to_address: '0x...',
  amount: '1000000000000000000'
})
```

## Development

### Development Server

For development with hot reload:

```bash
cd web
npm install
npm run dev
```

This starts a development server at `http://localhost:5173` with hot module replacement.

### Production Build

```bash
npm run build
```

Output is generated in `web/dist/` and should be copied to the node's static directory.

## Troubleshooting

### Dashboard Not Loading

**Problem:** Visiting `http://localhost:8082` shows JSON instead of the dashboard.

**Solution:** Build the dashboard first:

```bash
python scripts/build_dashboard.py
```

### WebSocket Connection Failed

**Problem:** Real-time updates not working.

**Causes:**
- Node not running
- Firewall blocking WebSocket connections
- Browser mixed content policy (HTTPS page with WS connection)

**Solution:** Ensure the node is running and accessible on port 8082.

### API Errors

**Problem:** API requests returning errors.

**Solution:** Check the node logs for detailed error messages:

```bash
# View node logs
poetry run python -m datamgmtnode.main --log-level DEBUG
```

## See Also

- [Terminal UI](terminal-ui.md) - Command-line dashboard alternative
- [API Reference](api-reference.md) - Complete API documentation
- [Monitoring](../operations/monitoring.md) - Production monitoring setup
