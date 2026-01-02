# P2P Network

DataMgmt Node uses a Kademlia-based peer-to-peer network for decentralized data distribution.

## Overview

The P2P network provides:

- **Peer Discovery** - Automatic discovery of other nodes
- **Data Distribution** - Store and retrieve data across the network
- **Health Monitoring** - Track peer availability and performance
- **Resilience** - Continue operating even when peers go offline

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                      P2P Network Layer                       │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────┐  │
│  │   Kademlia  │  │   Peer      │  │    Health           │  │
│  │     DHT     │  │   Manager   │  │    Monitor          │  │
│  └──────┬──────┘  └──────┬──────┘  └──────────┬──────────┘  │
│         │                │                     │             │
│  ┌──────┴────────────────┴─────────────────────┴──────────┐  │
│  │                    Peer Storage                         │  │
│  │              (known_peers.json)                         │  │
│  └────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

## Configuration

### Bootstrap Peers

Configure initial peers to connect to:

```bash
# .env
INITIAL_PEERS=http://bootstrap1.datamgmt.io:8000,http://bootstrap2.datamgmt.io:8000
```

### P2P Port

Set the port for P2P communication:

```bash
P2P_PORT=8000
```

!!! warning "Firewall Configuration"
    Ensure your firewall allows incoming connections on the P2P port for full network participation.

## Peer Discovery

### How It Works

1. **Bootstrap** - Node connects to initial peers from configuration
2. **Exchange** - Peers share their known peer lists
3. **Health Check** - Peers are periodically checked for availability
4. **Pruning** - Dead peers are removed from the network

### Peer Exchange

Every 5 minutes, nodes exchange peer lists:

```
Node A                    Node B
   │                         │
   │── Request Peer List ──>│
   │                         │
   │<── Peer List Response ──│
   │                         │
   │── Share Own Peers ────>│
   │                         │
```

## Network Statistics

### View Stats

Get network statistics via the API:

```bash
curl http://localhost:8081/network/stats
```

**Response:**

```json
{
  "total_peers": 15,
  "healthy_peers": 12,
  "data_sent": 10485760,
  "data_received": 5242880,
  "uptime": 86400
}
```

### View Peers

List connected peers:

```bash
# All peers
curl http://localhost:8081/network/peers

# Healthy peers only
curl "http://localhost:8081/network/peers?healthy=true"
```

**Response:**

```json
{
  "peers": [
    "192.168.1.10:8000",
    "10.0.0.5:8000",
    "172.16.0.20:8000"
  ],
  "count": 3
}
```

## Peer Health

### Health Criteria

A peer is considered healthy if:

- Responded within the last 5 minutes
- Has a success rate above 50%
- Or has fewer than 5 total attempts (new peer)

### Health Monitoring

The node continuously monitors peer health:

```
┌─────────────────────────────────────┐
│         Health Check Loop           │
├─────────────────────────────────────┤
│  Every 60 seconds:                  │
│  1. Check each peer's last response │
│  2. Ping unresponsive peers         │
│  3. Update success/failure counts   │
│  4. Prune dead peers (>1 hour old)  │
└─────────────────────────────────────┘
```

## Data Distribution

### Sending Data

When you share data, it's distributed to the network:

```python
# Internal flow
async def send_data(data_hash, data):
    # Store in local DHT
    await dht.set(data_hash, data)

    # Broadcast to healthy peers
    for peer in get_healthy_peers():
        await send_to_peer(peer, data_hash, data)
```

### Retrieving Data

Data retrieval checks local storage first, then the network:

```python
async def get_data(data_hash):
    # Try local storage first
    data = local_storage.get(data_hash)
    if data:
        return data

    # Query the DHT network
    return await dht.get(data_hash)
```

## Persistence

### Peer Storage

Known peers are persisted to `known_peers.json`:

```json
{
  "192.168.1.10:8000": {
    "host": "192.168.1.10",
    "port": 8000,
    "last_seen": 1705312200.5,
    "success_count": 100,
    "failure_count": 5
  }
}
```

### Automatic Re-Bootstrap

If the node loses all peers, it will:

1. Wait 30 seconds
2. Reconnect to bootstrap peers
3. Begin peer discovery again

## Troubleshooting

### No Peers Connected

**Symptoms:**

```json
{
  "total_peers": 0,
  "healthy_peers": 0
}
```

**Solutions:**

1. Check `INITIAL_PEERS` configuration
2. Verify firewall allows P2P port
3. Check bootstrap peer availability
4. Review logs for connection errors

### High Peer Failure Rate

**Symptoms:**

- Many unhealthy peers
- Slow data retrieval

**Solutions:**

1. Check network connectivity
2. Verify peers are running compatible versions
3. Monitor for network partitions

### Data Not Found

**Symptoms:**

- `404 Data not found` errors
- Long retrieval times

**Solutions:**

1. Verify data was shared successfully
2. Check peer connectivity
3. Wait for network propagation
4. Increase peer count

## Best Practices

### Network Health

- Maintain connections to multiple bootstrap nodes
- Monitor peer counts and health rates
- Set up alerts for network degradation

### Performance

- Use geographic diversity in bootstrap peers
- Keep P2P port accessible
- Monitor bandwidth usage

### Security

- Use authenticated connections where possible
- Monitor for suspicious peer behavior
- Regularly rotate node identity if needed

## Next Steps

- [API Reference](api-reference.md) - Network API endpoints
- [Monitoring Guide](../operations/monitoring.md) - Network monitoring
- [Security Guide](../operations/security.md) - Network security
