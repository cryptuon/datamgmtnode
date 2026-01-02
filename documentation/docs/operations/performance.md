# Performance Tuning

Optimize DataMgmt Node for production workloads. This guide covers configuration, monitoring, and optimization strategies.

## System Requirements

### Minimum Requirements

| Component | Minimum | Recommended |
|-----------|---------|-------------|
| CPU | 2 cores | 4+ cores |
| RAM | 2 GB | 8+ GB |
| Storage | 20 GB SSD | 100+ GB NVMe |
| Network | 10 Mbps | 100+ Mbps |

### Storage Considerations

- **SSD required** - RocksDB/LevelDB performance degrades significantly on HDD
- **NVMe recommended** - For high-throughput data operations
- **Separate volumes** - Consider separate storage for database and logs

## Database Tuning

### RocksDB vs LevelDB

The node supports two storage backends:

| Backend | Pros | Cons |
|---------|------|------|
| **RocksDB** | Better compression, higher throughput | Higher memory usage |
| **LevelDB** | Lower memory, simpler | Lower throughput |

RocksDB is used automatically if available; otherwise falls back to LevelDB.

### Installing RocksDB

```bash
# Ubuntu/Debian
sudo apt install librocksdb-dev

# macOS
brew install rocksdb

# Python bindings
pip install python-rocksdb
```

### Database Path Configuration

Use fast storage for the database:

```bash
# .env
DB_PATH=/var/lib/datamgmt/nodedb  # SSD/NVMe mount
```

## P2P Network Tuning

### Connection Parameters

The P2P network has configurable intervals:

| Parameter | Default | Description |
|-----------|---------|-------------|
| Health check interval | 60s | How often to check peer health |
| Peer exchange interval | 120s | How often to share peer lists |
| Re-bootstrap interval | 300s | How often to check peer count |
| Minimum peers | 3 | Trigger re-bootstrap below this |

### Optimizing for High Peer Count

For nodes with many connections:

```python
# In p2p_network.py customization
self._health_check_interval = 120  # Less frequent checks
self._peer_exchange_interval = 300  # Less frequent exchanges
```

### Bootstrap Node Strategy

For better network connectivity:

```bash
# .env - Multiple bootstrap nodes
INITIAL_PEERS=http://node1.example.com:8000,http://node2.example.com:8000,http://node3.example.com:8000
```

### Peer Health Thresholds

Peers are considered healthy when:

- Last seen within 300 seconds (5 minutes)
- Success rate > 50% OR fewer than 3 attempts

## API Rate Limiting

### Default Limits

| API | Rate | Burst |
|-----|------|-------|
| Internal API | 50 req/s | 100 |
| External API | 10 req/s | 20 |

### Adjusting Limits

Modify in `api/rate_limiter.py`:

```python
# Higher limits for internal use
internal_limiter = RateLimiter(
    rate=100,   # requests per second
    burst=200   # burst allowance
)

# Stricter limits for public API
external_limiter = RateLimiter(
    rate=20,
    burst=40
)
```

### Per-Client Tracking

Rate limits are tracked per client IP. For proxied requests, configure headers:

```python
# Supported headers (in order of precedence)
X-Forwarded-For
X-Real-IP
```

## Memory Optimization

### Event Bus History

Control event history size:

```python
# In node.py
self.event_bus = EventBus(max_history=50)  # Default 100
```

### WebSocket Event Buffer

Limit events stored per WebSocket client:

```javascript
// In useWebSocket.js
if (events.value.length > 50) {  // Default 100
    events.value.shift()
}
```

### Data Manager Caching

For high-volume data operations, consider caching layers:

```python
# Example: Add LRU cache for frequently accessed data
from functools import lru_cache

@lru_cache(maxsize=1000)
def get_cached_data(data_hash):
    return data_manager.get_data(data_hash)
```

## Encryption Performance

### Key Manager Optimization

Key derivation uses PBKDF2 with 480,000 iterations. This is secure but slow for initial key generation:

```python
# In key_manager.py - Current settings
iterations = 480000  # Secure default
```

!!! warning
    Do not reduce iterations in production. The one-time cost at startup is acceptable.

### Fernet Encryption

Fernet (symmetric encryption) is efficient for data operations:

- Encryption: ~1ms per KB
- Decryption: ~1ms per KB

For very large data, consider chunking:

```python
CHUNK_SIZE = 64 * 1024  # 64KB chunks

def encrypt_large_data(data):
    chunks = [data[i:i+CHUNK_SIZE] for i in range(0, len(data), CHUNK_SIZE)]
    return [cipher.encrypt(chunk) for chunk in chunks]
```

## Blockchain Optimization

### RPC Connection

Use a reliable, low-latency RPC provider:

| Provider | Latency | Notes |
|----------|---------|-------|
| Local node | <10ms | Best performance, highest cost |
| Infura/Alchemy | 50-100ms | Good balance |
| Public RPC | 100-500ms | Free but unreliable |

### Gas Optimization

For compliance recording:

```python
# Use efficient gas settings
transaction['gas'] = 50000  # Minimal for data storage
transaction['gasPrice'] = web3.eth.gas_price  # Current price
```

### Batch Operations

For multiple token transfers:

```python
# Instead of individual calls
for transfer in transfers:
    process_payment(transfer)

# Consider multicall patterns
# (requires custom contract)
```

## Dashboard Performance

### WebSocket Optimization

Reduce update frequency for large deployments:

```python
# In node.py - Status update loop
await asyncio.sleep(30)  # Increase from 10s to 30s
```

### Web Dashboard Build

Optimize the Vue.js build:

```bash
# Production build with minification
cd web
npm run build -- --mode production
```

### TUI Refresh Rate

The TUI refreshes on events. For quiet networks, reduce polling:

```python
# In TUI api_client.py
self.poll_interval = 5  # seconds between API polls
```

## Monitoring Performance

### Key Metrics

Monitor these for performance issues:

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU usage | >70% | >90% |
| Memory usage | >70% | >85% |
| Disk I/O wait | >20% | >50% |
| P2P latency | >500ms | >2000ms |
| API response time | >500ms | >2000ms |

### Profiling

Enable Python profiling:

```python
import cProfile
import pstats

profiler = cProfile.Profile()
profiler.enable()

# Run code to profile

profiler.disable()
stats = pstats.Stats(profiler)
stats.sort_stats('cumulative')
stats.print_stats(20)
```

### Async Performance

For async bottlenecks:

```python
import asyncio

# Check event loop health
loop = asyncio.get_event_loop()
print(f"Running tasks: {len(asyncio.all_tasks(loop))}")
```

## Scaling Strategies

### Vertical Scaling

- Add more CPU cores for parallel operations
- Increase RAM for larger caches
- Use faster storage (NVMe)

### Horizontal Scaling

For high availability:

```
                    ┌─────────────┐
                    │   Load      │
                    │  Balancer   │
                    └──────┬──────┘
           ┌───────────────┼───────────────┐
           │               │               │
    ┌──────▼─────┐  ┌──────▼─────┐  ┌──────▼─────┐
    │   Node 1   │  │   Node 2   │  │   Node 3   │
    │  (Primary) │  │ (Secondary)│  │ (Secondary)│
    └──────┬─────┘  └──────┬─────┘  └──────┬─────┘
           │               │               │
           └───────────────┴───────────────┘
                           │
                    ┌──────▼──────┐
                    │   Shared    │
                    │  Blockchain │
                    └─────────────┘
```

### Load Balancing

For the External API:

```nginx
# nginx.conf
upstream datamgmt {
    least_conn;
    server node1:8081;
    server node2:8081;
    server node3:8081;
}

server {
    listen 80;
    location / {
        proxy_pass http://datamgmt;
    }
}
```

## Benchmarking

### API Throughput

```bash
# Using wrk
wrk -t4 -c100 -d30s http://localhost:8081/health

# Using ab
ab -n 10000 -c 100 http://localhost:8081/health
```

### Data Operations

```python
import time

start = time.time()
for i in range(1000):
    node.data_manager.store_data(f"hash{i}", f"data{i}")
elapsed = time.time() - start

print(f"1000 writes in {elapsed:.2f}s ({1000/elapsed:.0f} ops/s)")
```

### P2P Network

```python
# Measure DHT operations
start = time.time()
await p2p_network.send_data("test_hash", "test_data")
data = await p2p_network.get_data("test_hash")
elapsed = time.time() - start

print(f"DHT round-trip: {elapsed*1000:.0f}ms")
```

## Production Checklist

- [ ] Using RocksDB (not LevelDB)
- [ ] SSD/NVMe storage for database
- [ ] Reliable RPC provider configured
- [ ] Rate limits appropriate for load
- [ ] Event history sized correctly
- [ ] Monitoring in place
- [ ] Log rotation configured
- [ ] Backup strategy implemented

## See Also

- [Deployment](deployment.md) - Production deployment
- [Monitoring](monitoring.md) - Setting up monitoring
- [Security](security.md) - Security hardening
