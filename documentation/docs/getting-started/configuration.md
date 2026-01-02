# Configuration

DataMgmt Node is configured through environment variables. Copy `.env.example` to `.env` and customize as needed.

## Environment Variables

### Security Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `KEY_MASTER_PASSWORD` | **Yes** | - | Master password for encrypting keys at rest. Use a strong, unique password. |

!!! danger "Critical Security Setting"
    The `KEY_MASTER_PASSWORD` protects your encryption keys. If lost, encrypted data cannot be recovered. Store this password securely!

### Blockchain Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `BLOCKCHAIN_TYPE` | No | `evm` | Blockchain type. Currently only `evm` is supported. |
| `BLOCKCHAIN_URL` | **Yes** | - | RPC endpoint URL (e.g., Infura, Alchemy) |
| `PRIVATE_KEY` | **Yes** | - | Private key for signing transactions |
| `NATIVE_TOKEN_ADDRESS` | No | `0x000...000` | Native token contract address |

Example configurations:

=== "Ethereum Mainnet"

    ```bash
    BLOCKCHAIN_TYPE=evm
    BLOCKCHAIN_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
    ```

=== "Polygon"

    ```bash
    BLOCKCHAIN_TYPE=evm
    BLOCKCHAIN_URL=https://polygon-rpc.com
    ```

=== "Local (Ganache)"

    ```bash
    BLOCKCHAIN_TYPE=evm
    BLOCKCHAIN_URL=http://localhost:8545
    ```

### Storage Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `DB_PATH` | No | `./data/nodedb` | Path for LevelDB/RocksDB storage |
| `SQLITE_DB_PATH` | No | `./data/sqlite.db` | Path for SQLite database |
| `DATA_DIR` | No | `./data` | Base directory for all data |

### P2P Network Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `P2P_PORT` | No | `8000` | Port for P2P communication |
| `INITIAL_PEERS` | No | - | Comma-separated list of bootstrap peer URLs |

Example:

```bash
P2P_PORT=8000
INITIAL_PEERS=http://peer1.example.com:8000,http://peer2.example.com:8000
```

### Node Identity

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `NODE_ID` | No | `node1` | Unique identifier for this node |
| `NODE_SIGNATURE` | No | - | Node signature for authorization |

### API Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `INTERNAL_API_HOST` | No | `localhost` | Host for internal API |
| `INTERNAL_API_PORT` | No | `8080` | Port for internal API |
| `EXTERNAL_API_HOST` | No | `0.0.0.0` | Host for external API |
| `EXTERNAL_API_PORT` | No | `8081` | Port for external API |

### Plugin Configuration

| Variable | Required | Default | Description |
|----------|----------|---------|-------------|
| `PLUGIN_DIR` | No | `./plugins` | Directory containing plugins |

## Complete Example

```bash
# .env

# Security
KEY_MASTER_PASSWORD=my-very-secure-master-password-2024!

# Blockchain
BLOCKCHAIN_TYPE=evm
BLOCKCHAIN_URL=https://mainnet.infura.io/v3/abc123def456
PRIVATE_KEY=0x1234567890abcdef...
NATIVE_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000

# Storage
DB_PATH=./data/nodedb
SQLITE_DB_PATH=./data/sqlite.db
DATA_DIR=./data

# P2P Network
P2P_PORT=8000
INITIAL_PEERS=http://bootstrap1.datamgmt.io:8000,http://bootstrap2.datamgmt.io:8000

# Node Identity
NODE_ID=production-node-1
NODE_SIGNATURE=

# Plugins
PLUGIN_DIR=./plugins
```

## Configuration Validation

The node validates configuration on startup. Invalid configuration will prevent the node from starting:

```
2024-01-15 10:30:00 - ERROR - Configuration error: Configuration validation failed:
  - blockchain_url is required
  - p2p_port must be an integer between 1 and 65535, got: 70000
```

### Validated Settings

The following settings are validated:

- `BLOCKCHAIN_TYPE` must be `evm`
- `BLOCKCHAIN_URL` must start with `http://`, `https://`, `ws://`, or `wss://`
- `NATIVE_TOKEN_ADDRESS` must be a valid Ethereum address (if provided)
- `P2P_PORT` must be between 1 and 65535
- `NODE_ID` must be 100 characters or less
- `INITIAL_PEERS` URLs must start with `http://` or `https://`

## Runtime Configuration

Some settings can be changed at runtime via the Internal API:

### Change Blockchain

```bash
curl -X POST http://localhost:8080/change_blockchain \
  -H "Content-Type: application/json" \
  -d '{
    "blockchain_type": "evm",
    "blockchain_url": "https://polygon-rpc.com",
    "private_key": "0x..."
  }'
```

### Add Token Support

```bash
curl -X POST http://localhost:8080/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
    "abi": [...]
  }'
```

## Next Steps

- [Security Best Practices](../operations/security.md) - Secure your configuration
- [Deployment Guide](../operations/deployment.md) - Production deployment
