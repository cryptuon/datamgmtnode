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
  "data_sent": 10485760,
  "data_received": 5242880,
  "uptime": 86400
}
```

### Key Metrics to Monitor

| Metric | Description | Alert Threshold |
|--------|-------------|-----------------|
| `healthy_peers` | Connected healthy peers | < 3 |
| `total_peers` | Total known peers | < 5 |
| `uptime` | Node uptime in seconds | - |
| `data_sent` | Bytes sent | - |
| `data_received` | Bytes received | - |

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

## Prometheus Integration

### Expose Metrics

Add a metrics endpoint (custom implementation required):

```python
# Example metrics endpoint
from prometheus_client import Counter, Gauge, generate_latest

requests_total = Counter('datamgmt_requests_total', 'Total requests', ['endpoint'])
peers_connected = Gauge('datamgmt_peers_connected', 'Connected peers')
data_operations = Counter('datamgmt_data_operations', 'Data operations', ['type'])
```

### Prometheus Configuration

```yaml
# prometheus.yml
scrape_configs:
  - job_name: 'datamgmt-node'
    static_configs:
      - targets: ['localhost:9090']
    scrape_interval: 15s
```

### Grafana Dashboard

Import a dashboard with these panels:

1. **Node Health** - Health status over time
2. **Peer Connections** - Connected vs healthy peers
3. **Data Operations** - Shares, retrievals, verifications
4. **API Latency** - Request response times
5. **Error Rate** - Errors by type

## Alerting

### Alert Rules

```yaml
# alerts.yml
groups:
- name: datamgmt
  rules:
  - alert: NodeUnhealthy
    expr: datamgmt_health_status != 1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: "DataMgmt node is unhealthy"

  - alert: LowPeerCount
    expr: datamgmt_peers_connected < 3
    for: 10m
    labels:
      severity: warning
    annotations:
      summary: "Low peer count: {{ $value }}"

  - alert: HighErrorRate
    expr: rate(datamgmt_errors_total[5m]) > 0.1
    for: 5m
    labels:
      severity: warning
    annotations:
      summary: "High error rate detected"

  - alert: BlockchainDisconnected
    expr: datamgmt_blockchain_connected == 0
    for: 2m
    labels:
      severity: critical
    annotations:
      summary: "Blockchain connection lost"
```

### Notification Channels

Configure alerts to:

- Email
- Slack
- PagerDuty
- OpsGenie

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
