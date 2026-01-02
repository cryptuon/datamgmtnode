# API Reference

Complete reference for DataMgmt Node APIs.

## Overview

DataMgmt Node exposes three REST APIs:

| API | Default Port | Purpose |
|-----|--------------|---------|
| Internal API | 8080 | Node management, bound to localhost |
| External API | 8081 | Data sharing, publicly accessible |
| Dashboard API | 8082 | Web dashboard, TUI, WebSocket for real-time updates |

## Authentication

Protected endpoints require the `X-API-Key` header:

```bash
curl -H "X-API-Key: your-api-key" http://localhost:8081/share_data
```

## Rate Limiting

Both APIs implement rate limiting:

| API | Rate | Burst |
|-----|------|-------|
| Internal | 50 req/s | 100 |
| External | 10 req/s | 20 |

Rate limit exceeded responses:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 1.5
}
```

---

## Internal API (Port 8080)

### Health Check

Check node health status.

```
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "components": {
    "blockchain": "connected",
    "p2p_network": "running",
    "encryption": "initialized"
  },
  "version": "0.1.0"
}
```

| Status | Description |
|--------|-------------|
| `healthy` | All components operational |
| `degraded` | Some components have issues |
| `unhealthy` | Critical failure |

---

### Get Balance

Get token balance for an address.

```
GET /balance/{address}
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `address` | path | Ethereum address |

**Response:**

```json
{
  "address": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
  "balance": "1000000000000000000",
  "token": "0x0000000000000000000000000000000000000000"
}
```

---

### Transfer Tokens

Transfer tokens between addresses.

```
POST /transfer
```

**Request Body:**

```json
{
  "from": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
  "to": "0x853d35Cc6634C0532925a3b844Bc9e7595f1dE02",
  "amount": 1000000000000000000,
  "token": "0x0000000000000000000000000000000000000000"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `from` | string | Yes | Sender address |
| `to` | string | Yes | Recipient address |
| `amount` | integer | Yes | Amount in wei |
| `token` | string | Yes | Token contract address |

**Response:**

```json
{
  "success": true,
  "tx_hash": "0x1234567890abcdef...",
  "from": "0x742d...",
  "to": "0x853d...",
  "amount": "1000000000000000000"
}
```

---

### List Tokens

List all supported tokens.

```
GET /tokens
```

**Response:**

```json
{
  "tokens": [
    {
      "address": "0x0000000000000000000000000000000000000000",
      "type": "native",
      "symbol": "ETH"
    },
    {
      "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
      "type": "erc20"
    }
  ]
}
```

---

### Add Token

Add support for a new ERC-20 token.

```
POST /tokens
```

**Request Body:**

```json
{
  "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
  "abi": [...]
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `address` | string | Yes | Token contract address |
| `abi` | array | Yes | Contract ABI |

**Response:**

```json
{
  "success": true,
  "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F"
}
```

---

## External API (Port 8081)

### Health Check

Check external API health.

```
GET /health
```

**Response:**

```json
{
  "status": "healthy",
  "p2p": {
    "running": true,
    "peers": 5
  }
}
```

---

### Share Data

Share encrypted data with a recipient.

```
POST /share_data
```

**Headers:**

| Name | Required | Description |
|------|----------|-------------|
| `X-API-Key` | Yes | API key for authentication |
| `Content-Type` | Yes | Must be `application/json` |

**Request Body:**

```json
{
  "data": "Data to share",
  "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
  "payment_token": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
  "payment_amount": 1000000000000000000
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | string | Yes | Data to share (max 1MB) |
| `recipient` | string | Yes | Recipient Ethereum address |
| `payment_token` | string | No | Payment token address |
| `payment_amount` | integer | No | Payment amount in wei |

**Response:**

```json
{
  "success": true,
  "tx_hash": "0x1234567890abcdef...",
  "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
}
```

---

### Get Data

Retrieve shared data by hash.

```
GET /data/{data_hash}
```

**Headers:**

| Name | Required | Description |
|------|----------|-------------|
| `X-API-Key` | Yes | API key for authentication |

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `data_hash` | path | SHA-256 hash (64 hex chars) |

**Response:**

```json
{
  "hash": "abc123def456...",
  "data": "The shared data content"
}
```

**Errors:**

| Status | Description |
|--------|-------------|
| 401 | Unauthorized |
| 404 | Data not found |

---

### Verify Data

Verify data compliance on blockchain.

```
GET /verify_data/{data_hash}
```

**Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `data_hash` | path | SHA-256 hash (64 hex chars) |

**Response:**

```json
{
  "hash": "abc123def456...",
  "verified": true,
  "event_type": "data_share"
}
```

---

### Get Compliance History

Get compliance event history.

```
GET /compliance_history
```

**Query Parameters:**

| Name | Type | Description |
|------|------|-------------|
| `filters` | string | Comma-separated event types |

**Response:**

```json
{
  "history": [
    {
      "event_type": "data_share",
      "data_hash": "abc123...",
      "recipient": "0x742d...",
      "timestamp": 1705312200,
      "tx_hash": "0x1234..."
    }
  ],
  "count": 1,
  "filters": ["data_share"]
}
```

---

### Get Network Stats

Get P2P network statistics.

```
GET /network/stats
```

**Response:**

```json
{
  "total_peers": 10,
  "healthy_peers": 8,
  "data_sent": 1048576,
  "data_received": 524288,
  "uptime": 86400
}
```

---

### Get Peers

Get list of connected peers.

```
GET /network/peers
```

**Query Parameters:**

| Name | Type | Default | Description |
|------|------|---------|-------------|
| `healthy` | boolean | `false` | Only return healthy peers |

**Response:**

```json
{
  "peers": [
    "192.168.1.10:8000",
    "10.0.0.5:8000"
  ],
  "count": 2
}
```

---

## Error Responses

All APIs use consistent error responses:

### Validation Error (422)

```json
{
  "error": "recipient must be a valid Ethereum address",
  "field": "recipient"
}
```

### Unauthorized (401)

```json
{
  "error": "Unauthorized. Provide valid X-API-Key header."
}
```

### Not Found (404)

```json
{
  "error": "Data not found"
}
```

### Rate Limited (429)

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 1.5
}
```

### Internal Error (500)

```json
{
  "error": "Internal server error"
}
```

---

## Dashboard API (Port 8082)

The Dashboard API provides a unified interface for the web dashboard and TUI, including WebSocket support for real-time updates.

### Dashboard Info

Get dashboard-specific information.

```
GET /api/dashboard/info
```

**Response:**

```json
{
  "node_id": "node1",
  "websocket_clients": 2,
  "event_history_size": 45,
  "api_version": "1.0.0",
  "ports": {
    "internal_api": 8080,
    "external_api": 8081,
    "dashboard": 8082
  }
}
```

---

### WebSocket Connection

Connect for real-time event streaming.

```
GET /ws
```

Upgrade to WebSocket connection. Once connected, the server sends:

1. Connection acknowledgment
2. Recent event history (last 20 events)
3. Real-time events as they occur

**Connection Message:**

```json
{
  "type": "connected",
  "data": {
    "message": "WebSocket connection established",
    "history_available": 45
  }
}
```

**Event Message Format:**

```json
{
  "type": "token.transfer_completed",
  "data": {
    "from": "0x742d...",
    "to": "0x853d...",
    "amount": "1000000000000000000"
  },
  "timestamp": 1705312200.123
}
```

### WebSocket Client Messages

**Ping:**

```json
{"type": "ping"}
```

Response: `{"type": "pong"}`

**Request History:**

```json
{"type": "get_history", "count": 50}
```

Response:

```json
{
  "type": "history",
  "data": {
    "events": [...],
    "count": 50
  }
}
```

---

### Event Types

Events broadcast via WebSocket:

| Event Type | Description |
|------------|-------------|
| `health.update` | Node health status changed |
| `health.component_change` | Individual component status changed |
| `token.balance_update` | Token balance changed |
| `token.transfer_completed` | Token transfer succeeded |
| `token.transfer_failed` | Token transfer failed |
| `token.added` | New token added to supported list |
| `data.shared` | Data was shared with recipient |
| `data.received` | Data was received from peer |
| `data.verified` | Data compliance was verified |
| `compliance.event` | Compliance event recorded |
| `network.peer_connected` | New peer connected |
| `network.peer_disconnected` | Peer disconnected |
| `network.peer_health` | Peer health status updated |
| `network.stats_update` | Network statistics updated |
| `system.node_started` | Node started |
| `system.node_stopping` | Node shutting down |
| `system.error` | System error occurred |

---

### Proxied Endpoints

The Dashboard API also proxies all Internal and External API endpoints under the `/api` prefix:

| Endpoint | Proxied From |
|----------|--------------|
| `GET /api/health` | Internal API |
| `GET /api/balance/{address}` | Internal API |
| `POST /api/transfer` | Internal API |
| `GET /api/tokens` | Internal API |
| `POST /api/tokens` | Internal API |
| `POST /api/share_data` | External API |
| `GET /api/data/{data_hash}` | External API |
| `GET /api/verify_data/{data_hash}` | External API |
| `GET /api/compliance_history` | External API |
| `GET /api/network/stats` | External API |
| `GET /api/network/peers` | External API |

This allows web dashboard and TUI to access all node functionality through a single endpoint.
