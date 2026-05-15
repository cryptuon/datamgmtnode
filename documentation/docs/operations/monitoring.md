# Monitoring

Monitor your DataMgmt Node deployment for health, performance, and security.

## Health Checks

### Endpoints

Both APIs expose health check endpoints:

| Endpoint | Port | Description |
|----------|------|-------------|
| `GET /health` | 8080 | Internal API health |
| `GET /health` | 8081 | External API health |

### Internal API Health

```bash
curl http://localhost:8080/health
```

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

### External API Health

```bash
curl http://localhost:8081/health
```

```json
{
  "status": "healthy",
  "p2p": {
    "running": true,
    "peers": 12
  }
}
```

### Health Status Values

| Status | Description |
|--------|-------------|
| `healthy` | All components operational |
| `degraded` | Some components have issues |
| `unhealthy` | Critical failure |

## Metrics

### Network Statistics

```bash
curl http://localhost:8081/network/stats
```

```json
{
  "total_peers": 15,
  "healthy_peers": 12,
  "active_peers": 11,
  "bootstrap_nodes": 2,
  "avg_latency_ms": 92.3
}
```

### Key Metrics to Monitor

(Field names match `P2PNetwork.get_network_stats`,
`datamgmtnode/network/p2p_network.py:518`.)

| Metric | Description | Suggested Alert |
|--------|-------------|-----------------|
| `healthy_peers` | Peers passing health check | `< 3` triggers re-bootstrap loop |
| `total_peers` | All known peers (any health) | `< 5` warning |
| `active_peers` | Peers in the live Kademlia routing table | `< _min_peers` |
| `avg_latency_ms` | Mean latency across healthy peers | `> 500ms` warning |

## Logging

### Log Configuration

Logs are written to stdout with the format:

```
2024-01-15 10:30:00 - module_name - INFO - Log message
```

### Log Levels

| Level | Description |
|-------|-------------|
| `DEBUG` | Detailed debugging information |
| `INFO` | Normal operation events |
| `WARNING` | Unexpected but handled events |
| `ERROR` | Errors that need attention |

### Important Log Messages

**Startup:**
```
INFO - Configuration validated successfully
INFO - Node started successfully
INFO - P2P Network started on port 8000
```

**Peer Events:**
```
INFO - Connected to peer 192.168.1.10:8000
WARNING - Peer 10.0.0.5:8000 marked unhealthy
INFO - Discovered 5 new peers
```

**Data Operations:**
```
INFO - Received data with hash: abc123...
INFO - Data share recorded: tx_hash=0x1234...
```

**Errors:**
```
ERROR - Failed to connect to blockchain: Connection refused
ERROR - Authorization verification failed: Invalid signature
WARNING - Rate limit exceeded for 192.168.1.100
```

## Polling-Based Alerting

The node currently does **not** expose Prometheus metrics — there is no
`/metrics` endpoint and `prometheus_client` is not a dependency. Treat any
metric system as built on top of the JSON endpoints above.

A minimal blackbox-style approach:

```bash
# Pseudo-alert script (run from cron / systemd timer)
status=$(curl -s http://localhost:8080/health | jq -r .status)
if [ "$status" != "healthy" ]; then
  notify "DataMgmt node status: $status"
fi

healthy=$(curl -s http://localhost:8081/network/stats | jq -r .healthy_peers)
if [ "$healthy" -lt 3 ]; then
  notify "DataMgmt peer count low: $healthy"
fi
```

For richer telemetry, write a small exporter that scrapes `/health`,
`/network/stats`, and `/api/dashboard/info` and republishes the values.

## Log Aggregation

### Fluentd Configuration

```xml
<source>
  @type tail
  path /var/log/datamgmt/*.log
  pos_file /var/log/fluentd/datamgmt.pos
  tag datamgmt
  <parse>
    @type regexp
    expression /^(?<time>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}) - (?<module>\S+) - (?<level>\S+) - (?<message>.*)$/
  </parse>
</source>

<match datamgmt.**>
  @type elasticsearch
  host elasticsearch
  port 9200
  index_name datamgmt
</match>
```

### ELK Stack Queries

Search for errors:
```
level:ERROR AND module:*
```

Search for specific operations:
```
message:"data share" AND level:INFO
```

## Uptime Monitoring

### External Monitoring

Configure external monitoring services:

```bash
# Health check endpoint
https://api.datamgmt.example.com/health

# Expected response
{"status": "healthy", ...}
```

### Uptime Checklist

- [ ] Health endpoint accessible externally
- [ ] Response time < 1 second
- [ ] Status returns "healthy"
- [ ] Check interval: 1 minute
- [ ] Alert after 3 failures

## Troubleshooting

### Common Issues

**Node won't start:**
```bash
# Check logs
journalctl -u datamgmt-node -f

# Verify configuration
cat .env | grep -v PASSWORD
```

**No peers connecting:**
```bash
# Check network stats
curl http://localhost:8081/network/stats

# Verify firewall
sudo ufw status
```

**High memory usage:**
```bash
# Check process memory
ps aux | grep datamgmt

# Monitor over time
watch -n 5 'ps -o rss,vsz,pid,cmd -p $(pgrep -f datamgmt)'
```

### Debug Mode

Enable debug logging:

```python
# In main.py
logging.basicConfig(level=logging.DEBUG)
```

## Next Steps

- [Security Guide](security.md) - Security monitoring
- [Deployment Guide](deployment.md) - Production setup
