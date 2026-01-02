# Data Sharing

This guide covers all aspects of sharing data through DataMgmt Node.

## Basic Data Sharing

### Share Data

To share data with a recipient, send a POST request to the external API:

```bash
curl -X POST http://localhost:8081/share_data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "data": "Your data content here",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
  }'
```

**Request Body:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `data` | string | Yes | Data to share (max 1MB) |
| `recipient` | string | Yes | Ethereum address of recipient |
| `payment_token` | string | No | Token contract address |
| `payment_amount` | integer | No | Payment amount in wei |

**Response:**

```json
{
  "success": true,
  "tx_hash": "0x1234567890abcdef...",
  "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
}
```

### Retrieve Data

Retrieve shared data using its hash:

```bash
curl http://localhost:8081/data/abc123def456... \
  -H "X-API-Key: your-api-key"
```

**Response:**

```json
{
  "hash": "abc123def456...",
  "data": "Your data content here"
}
```

!!! info "Data Discovery"
    If the data isn't found locally, the node will automatically search the P2P network.

## Data with Payments

Include payment when sharing data for monetization:

```bash
curl -X POST http://localhost:8081/share_data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "data": "Premium data content",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
    "payment_token": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
    "payment_amount": 1000000000000000000
  }'
```

!!! note "Payment Amount"
    The `payment_amount` is in the token's smallest unit (e.g., wei for ETH, or the token's decimals).

### Supported Tokens

Check supported tokens:

```bash
curl http://localhost:8080/tokens
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

### Add Token Support

Add a new ERC-20 token:

```bash
curl -X POST http://localhost:8080/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
    "abi": [
      {"constant":true,"inputs":[{"name":"_owner","type":"address"}],...}
    ]
  }'
```

## Compliance Verification

### Verify Data

Verify a data share was recorded on the blockchain:

```bash
curl http://localhost:8081/verify_data/abc123def456...
```

**Response:**

```json
{
  "hash": "abc123def456...",
  "verified": true,
  "event_type": "data_share"
}
```

### Compliance History

Get the compliance event history:

```bash
# All events
curl http://localhost:8081/compliance_history

# Filtered events
curl "http://localhost:8081/compliance_history?filters=data_share,transfer"
```

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

## Data Lifecycle

### 1. Data Creation

When you share data:

```python
import requests

response = requests.post(
    "http://localhost:8081/share_data",
    headers={"X-API-Key": "key"},
    json={
        "data": "Important document content",
        "recipient": "0x742d..."
    }
)

result = response.json()
tx_hash = result["tx_hash"]
```

### 2. Data Distribution

The data is automatically:

- Encrypted with the current encryption key
- Stored in local LevelDB/RocksDB
- Distributed to connected P2P peers
- Recorded on the blockchain for compliance

### 3. Data Retrieval

Recipients can retrieve data:

```python
# Compute or receive the data hash
data_hash = "abc123..."

# Retrieve the data
response = requests.get(
    f"http://localhost:8081/data/{data_hash}",
    headers={"X-API-Key": "key"}
)

data = response.json()["data"]
```

### 4. Data Verification

Verify the data sharing was compliant:

```python
response = requests.get(
    f"http://localhost:8081/verify_data/{data_hash}"
)

assert response.json()["verified"] == True
```

## Error Handling

### Validation Errors

Invalid requests return 422 with details:

```json
{
  "error": "recipient must be a valid Ethereum address (0x + 40 hex chars)",
  "field": "recipient"
}
```

### Authorization Errors

Unauthorized requests return 401:

```json
{
  "error": "Unauthorized. Provide valid X-API-Key header."
}
```

### Not Found Errors

Missing data returns 404:

```json
{
  "error": "Data not found"
}
```

### Rate Limiting

Exceeded rate limits return 429:

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 1.5
}
```

## Best Practices

### Data Size

- Keep individual data shares under 1MB
- For larger data, consider chunking or storing references

### Security

- Always use HTTPS in production
- Rotate API keys periodically
- Monitor compliance history for unauthorized access

### Performance

- Use connection pooling for multiple requests
- Cache frequently accessed data locally
- Monitor P2P network health

## Next Steps

- [API Reference](api-reference.md) - Complete endpoint documentation
- [P2P Network](p2p-network.md) - Network configuration
- [Security Guide](../operations/security.md) - Security best practices
