# Troubleshooting

Common issues and solutions for DataMgmt Node.

## Quick Diagnostics

Run these commands to quickly diagnose issues:

```bash
# Check if node is running
curl http://localhost:8080/health

# Check external API
curl http://localhost:8081/health

# Check dashboard API
curl http://localhost:8082/api/health

# Check network status
curl http://localhost:8081/network/stats

# View recent logs
journalctl -u datamgmt-node -n 100 --no-pager
```

## Startup Issues

### Node Won't Start

**Symptom:** Node exits immediately or shows configuration errors.

**Check configuration:**

```bash
# Verify .env file exists
cat .env

# Check for syntax errors
python -c "from dotenv import load_dotenv; load_dotenv()"
```

**Common causes:**

| Error Message | Cause | Solution |
|---------------|-------|----------|
| `blockchain_url is required` | Missing URL | Add `BLOCKCHAIN_URL` to .env |
| `Invalid native_token_address` | Wrong format | Use `0x` + 40 hex characters |
| `p2p_port must be between 1-65535` | Invalid port | Use valid port number |
| `Cannot create db_path directory` | Permission denied | Check directory permissions |

**Solution:**

```bash
# Validate configuration
poetry run python -c "
from datamgmtnode.services.node import NodeConfig
import os
from dotenv import load_dotenv
load_dotenv()

config = NodeConfig(
    blockchain_type=os.getenv('BLOCKCHAIN_TYPE', 'evm'),
    blockchain_url=os.getenv('BLOCKCHAIN_URL'),
    private_key=os.getenv('PRIVATE_KEY'),
    native_token_address=os.getenv('NATIVE_TOKEN_ADDRESS'),
    db_path=os.getenv('DB_PATH', './data/nodedb'),
    sqlite_db_path=os.getenv('SQLITE_DB_PATH', './data/sqlite.db'),
    p2p_port=int(os.getenv('P2P_PORT', 8000)),
    plugin_dir=os.getenv('PLUGIN_DIR', './plugins'),
    node_id=os.getenv('NODE_ID', 'node1'),
    node_signature=os.getenv('NODE_SIGNATURE', ''),
    initial_peers=os.getenv('INITIAL_PEERS', '').split(',') if os.getenv('INITIAL_PEERS') else []
)
config.validate()
print('Configuration valid!')
"
```

### Blockchain Connection Failed

**Symptom:** `Failed to connect to the blockchain` error.

**Causes:**

1. Invalid RPC URL
2. RPC endpoint unreachable
3. Network issues

**Diagnosis:**

```bash
# Test RPC endpoint
curl -X POST -H "Content-Type: application/json" \
  --data '{"jsonrpc":"2.0","method":"eth_blockNumber","params":[],"id":1}' \
  $BLOCKCHAIN_URL
```

**Solutions:**

```bash
# Check URL format
# Valid: https://mainnet.infura.io/v3/YOUR_KEY
# Valid: http://localhost:8545
# Invalid: mainnet.infura.io (missing protocol)

# Test with web3
poetry run python -c "
from web3 import Web3
w3 = Web3(Web3.HTTPProvider('$BLOCKCHAIN_URL'))
print(f'Connected: {w3.is_connected()}')
print(f'Block: {w3.eth.block_number}')
"
```

### Port Already in Use

**Symptom:** `Address already in use` error.

**Diagnosis:**

```bash
# Check what's using the ports
lsof -i :8080  # Internal API
lsof -i :8081  # External API
lsof -i :8082  # Dashboard API
lsof -i :8000  # P2P network
```

**Solutions:**

```bash
# Kill existing process
kill $(lsof -t -i:8080)

# Or change ports in .env
INTERNAL_API_PORT=8090
EXTERNAL_API_PORT=8091
DASHBOARD_API_PORT=8092
P2P_PORT=8001
```

## P2P Network Issues

### No Peers Connecting

**Symptom:** `total_peers: 0` in network stats.

**Diagnosis:**

```bash
# Check network stats
curl http://localhost:8081/network/stats

# Check known peers file
cat data/known_peers.json
```

**Causes and solutions:**

| Cause | Solution |
|-------|----------|
| No bootstrap peers | Add `INITIAL_PEERS` to .env |
| Firewall blocking | Open UDP port (default 8000) |
| NAT issues | Configure port forwarding |
| Peers offline | Try different bootstrap nodes |

**Firewall configuration:**

```bash
# Ubuntu/Debian
sudo ufw allow 8000/udp

# CentOS/RHEL
sudo firewall-cmd --add-port=8000/udp --permanent
sudo firewall-cmd --reload
```

### Peers Disconnecting

**Symptom:** Peers connect but quickly disconnect.

**Check peer health:**

```bash
curl http://localhost:8081/network/peers | python -m json.tool
```

**Causes:**

1. **Network instability** - Check internet connection
2. **Timeouts** - Increase health check interval
3. **Incompatible versions** - Ensure same node version

### High Latency

**Symptom:** `avg_latency_ms` > 500ms.

**Solutions:**

1. Use geographically closer bootstrap nodes
2. Check network bandwidth
3. Reduce concurrent connections

## API Issues

### Rate Limit Exceeded

**Symptom:** `429 Too Many Requests` responses.

```json
{
  "error": "Rate limit exceeded",
  "retry_after": 1.5
}
```

**Solutions:**

1. Wait for `retry_after` seconds
2. Implement client-side rate limiting
3. Increase server rate limits (see Performance Tuning)

### Authentication Failed

**Symptom:** `401 Unauthorized` on external API.

**Check:**

```bash
# Ensure X-API-Key header is set
curl -H "X-API-Key: your-api-key" http://localhost:8081/share_data
```

**Solutions:**

1. Verify API key is correct
2. Check header name (case-sensitive: `X-API-Key`)
3. Ensure endpoint requires authentication

### Validation Errors

**Symptom:** `422 Unprocessable Entity` responses.

```json
{
  "error": "recipient must be a valid Ethereum address",
  "field": "recipient"
}
```

**Common validation errors:**

| Field | Requirement | Example |
|-------|-------------|---------|
| `address` | 0x + 40 hex chars | `0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01` |
| `amount` | Positive integer | `1000000000000000000` |
| `data` | Max 1MB string | Any string < 1MB |
| `data_hash` | 64 hex chars | SHA-256 hash |

## Data Operations

### Data Not Found

**Symptom:** `404 Not Found` when retrieving data.

**Diagnosis:**

```bash
# Check if data exists locally
poetry run python -c "
from datamgmtnode.services.data_manager import DataManager
dm = DataManager('./data/nodedb')
print(dm.get_data('your_data_hash'))
"
```

**Causes:**

1. Data never stored
2. Wrong hash
3. Data not yet replicated from network

**Solutions:**

```bash
# Wait for P2P replication
sleep 30 && curl http://localhost:8081/data/$DATA_HASH

# Verify hash calculation
poetry run python -c "
import hashlib
data = 'your data'
print(hashlib.sha256(data.encode()).hexdigest())
"
```

### Encryption/Decryption Errors

**Symptom:** `InvalidToken` or garbled data.

**Causes:**

1. Wrong encryption key
2. Data corrupted
3. Key rotation issues

**Check key version:**

```bash
# View current key version
poetry run python -c "
from datamgmtnode.services.key_manager import KeyManager
km = KeyManager('./data')
km.initialize()
print(f'Key version: {km.current_version}')
"
```

**Solutions:**

1. Ensure same `KEY_MASTER_PASSWORD` as when data was encrypted
2. Check for data corruption in storage
3. For rotated keys, ensure old keys are preserved

### Compliance Verification Failed

**Symptom:** `verified: false` for known operations.

**Causes:**

1. Transaction not yet mined
2. Wrong blockchain network
3. Event hash mismatch

**Diagnosis:**

```bash
# Check transaction on block explorer
# Etherscan, Polygonscan, etc.

# Verify blockchain connection
curl http://localhost:8080/health | grep blockchain
```

## Dashboard Issues

### Web Dashboard Not Loading

**Symptom:** Browser shows JSON instead of dashboard.

**Cause:** Dashboard not built.

**Solution:**

```bash
# Build the dashboard
python scripts/build_dashboard.py

# Verify static files exist
ls datamgmtnode/dashboard/static/
```

### WebSocket Connection Failed

**Symptom:** Dashboard shows "Disconnected" or no real-time updates.

**Diagnosis:**

```bash
# Test WebSocket endpoint
curl -i -N -H "Connection: Upgrade" \
  -H "Upgrade: websocket" \
  -H "Sec-WebSocket-Key: test" \
  -H "Sec-WebSocket-Version: 13" \
  http://localhost:8082/ws
```

**Causes:**

1. Node not running
2. Firewall blocking WebSocket
3. Proxy not configured for WebSocket

**Nginx proxy fix:**

```nginx
location /ws {
    proxy_pass http://localhost:8082;
    proxy_http_version 1.1;
    proxy_set_header Upgrade $http_upgrade;
    proxy_set_header Connection "upgrade";
}
```

### TUI Connection Failed

**Symptom:** "Failed to connect to Dashboard API" in TUI.

**Solutions:**

```bash
# Verify API is accessible
curl http://localhost:8082/api/health

# Start TUI with correct URL
poetry run python -m datamgmtnode.tui --api-url http://localhost:8082
```

## Token/Payment Issues

### Insufficient Balance

**Symptom:** Payment fails with balance error.

**Check balance:**

```bash
curl http://localhost:8080/balance/0xYourAddress
```

**Solutions:**

1. Fund account with tokens
2. Check correct token address
3. Verify amount in wei (multiply by 10^18)

### Transaction Failed

**Symptom:** Transaction submitted but fails on chain.

**Diagnosis:**

```python
# Get transaction receipt
from web3 import Web3
w3 = Web3(Web3.HTTPProvider(rpc_url))
receipt = w3.eth.get_transaction_receipt(tx_hash)
print(f"Status: {receipt.status}")  # 0 = failed
print(f"Gas used: {receipt.gasUsed}")
```

**Common causes:**

| Status | Cause | Solution |
|--------|-------|----------|
| Out of gas | Gas limit too low | Increase gas limit |
| Reverted | Contract error | Check function parameters |
| Nonce error | Transaction conflict | Reset nonce or wait |

### Token Not Recognized

**Symptom:** Token operations fail for custom tokens.

**Solution:**

```bash
# Add token with ABI
curl -X POST http://localhost:8080/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0xTokenAddress",
    "abi": [/* ERC20 ABI */]
  }'
```

## Performance Issues

### Slow Response Times

**Diagnosis:**

```bash
# Time API responses
time curl http://localhost:8080/health

# Check system resources
top -b -n 1 | head -20
```

**Solutions:**

1. Use SSD storage (see Performance Tuning)
2. Increase available memory
3. Check RPC endpoint latency

### High Memory Usage

**Diagnosis:**

```bash
# Check process memory
ps aux | grep datamgmt

# Detailed memory
python -c "
import psutil
p = psutil.Process()
print(f'RSS: {p.memory_info().rss / 1024 / 1024:.0f} MB')
"
```

**Solutions:**

1. Reduce event history size
2. Clear old data from database
3. Restart node periodically

### Database Errors

**Symptom:** LevelDB/RocksDB errors in logs.

**Solutions:**

```bash
# Check disk space
df -h

# Verify database permissions
ls -la data/nodedb/

# Repair database (backup first!)
poetry run python -c "
import plyvel
db = plyvel.DB('./data/nodedb', create_if_missing=False)
db.compact_range()
db.close()
"
```

## Getting Help

### Collect Diagnostic Information

Before requesting help, gather:

```bash
# System info
uname -a
python --version
poetry --version

# Node version
grep version pyproject.toml

# Configuration (redact secrets)
cat .env | grep -v KEY | grep -v PASSWORD

# Recent logs
journalctl -u datamgmt-node -n 500 > logs.txt

# Health status
curl http://localhost:8080/health > health.json
curl http://localhost:8081/network/stats > network.json
```

### Debug Mode

Enable verbose logging:

```python
# Set in your environment or main.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common Log Patterns

| Pattern | Meaning |
|---------|---------|
| `INFO - Node started successfully` | Normal startup |
| `WARNING - Peer marked unhealthy` | Network issue |
| `ERROR - Failed to connect` | Connection problem |
| `ERROR - Authorization verification failed` | Auth issue |

### Reporting Issues

When reporting issues, include:

1. Node version
2. Python version
3. Operating system
4. Error messages (full stack trace)
5. Steps to reproduce
6. Configuration (secrets redacted)

Report issues at: https://github.com/example/datamgmtnode/issues

## See Also

- [Monitoring](monitoring.md) - Set up monitoring
- [Performance](performance.md) - Performance tuning
- [Security](security.md) - Security configuration
