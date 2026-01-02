# Quick Start

Get up and running with DataMgmt Node in minutes.

## Start the Node

After [installation](installation.md), start your node:

```bash
cd datamgmtnode
poetry run python datamgmtnode/main.py
```

You should see:

```
2024-01-15 10:30:00 - __main__ - INFO - Configuration validated successfully
2024-01-15 10:30:01 - __main__ - INFO - Node started successfully
2024-01-15 10:30:01 - __main__ - INFO -   - Internal API: http://localhost:8080
2024-01-15 10:30:01 - __main__ - INFO -   - External API: http://0.0.0.0:8081
2024-01-15 10:30:01 - __main__ - INFO -   - P2P Port: 8000
2024-01-15 10:30:01 - __main__ - INFO - Press Ctrl+C to stop the node
```

## Check Node Health

Verify your node is running:

=== "curl"

    ```bash
    curl http://localhost:8080/health
    ```

=== "Python"

    ```python
    import requests

    response = requests.get("http://localhost:8080/health")
    print(response.json())
    ```

Response:

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

## Share Data

Share encrypted data with another participant:

=== "curl"

    ```bash
    curl -X POST http://localhost:8081/share_data \
      -H "Content-Type: application/json" \
      -H "X-API-Key: your-api-key" \
      -d '{
        "data": "Hello, secure world!",
        "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
      }'
    ```

=== "Python"

    ```python
    import requests

    response = requests.post(
        "http://localhost:8081/share_data",
        headers={
            "Content-Type": "application/json",
            "X-API-Key": "your-api-key"
        },
        json={
            "data": "Hello, secure world!",
            "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
        }
    )
    print(response.json())
    ```

Response:

```json
{
  "success": true,
  "tx_hash": "0x1234567890abcdef...",
  "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01"
}
```

## Retrieve Data

Retrieve shared data by its hash:

=== "curl"

    ```bash
    curl http://localhost:8081/data/abc123def456... \
      -H "X-API-Key: your-api-key"
    ```

=== "Python"

    ```python
    import requests

    data_hash = "abc123def456..."
    response = requests.get(
        f"http://localhost:8081/data/{data_hash}",
        headers={"X-API-Key": "your-api-key"}
    )
    print(response.json())
    ```

## Share Data with Payment

Include payment when sharing data:

```bash
curl -X POST http://localhost:8081/share_data \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{
    "data": "Premium data content",
    "recipient": "0x742d35Cc6634C0532925a3b844Bc9e7595f1dE01",
    "payment_token": "0x6B175474E89094C44Da98b954EescdeCB5F1c2d3",
    "payment_amount": 1000000000000000000
  }'
```

## View Network Statistics

Check your P2P network status:

```bash
curl http://localhost:8081/network/stats
```

Response:

```json
{
  "total_peers": 5,
  "healthy_peers": 4,
  "data_sent": 1024000,
  "data_received": 512000,
  "uptime": 3600
}
```

## Stop the Node

Press `Ctrl+C` to gracefully stop the node:

```
2024-01-15 11:30:00 - __main__ - INFO - Received signal SIGINT
2024-01-15 11:30:00 - __main__ - INFO - Shutting down node...
2024-01-15 11:30:01 - __main__ - INFO - Node stopped gracefully.
```

## Next Steps

- [Configuration Guide](configuration.md) - Customize your node
- [API Reference](../user-guide/api-reference.md) - Full API documentation
- [P2P Network](../user-guide/p2p-network.md) - Connect to more peers
