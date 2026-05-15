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

### API Ports

The three API ports are **hard-coded** in the source — they are not currently
read from environment variables, even though `.env.example` and
`deploy/entrypoint.sh` reference them:

| API | Port | Bind host | Defined at |
|-----|------|-----------|------------|
| Internal API | 8080 | `localhost` | `datamgmtnode/api/internal_api.py:32` |
| External API | 8081 | `0.0.0.0` | `datamgmtnode/api/external_api.py:36` |
| Dashboard API | 8082 | `0.0.0.0` | `datamgmtnode/api/dashboard_api.py:30,91` |

!!! warning "Contradiction in source"
    `INTERNAL_API_HOST`, `INTERNAL_API_PORT`, `EXTERNAL_API_HOST`,
    `EXTERNAL_API_PORT` appear in `.env.example` and `deploy/entrypoint.sh`,
    but `main.py` and the API constructors do not read them. Changing these
    values has no effect today; if you need different ports, patch the source
    or front the node with a reverse proxy (the bundled `deploy/nginx.conf`
    is one example).

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

The following are enforced by `NodeConfig.validate()`
(see `datamgmtnode/services/node.py:50`):

- `BLOCKCHAIN_TYPE` must be `evm`
- `BLOCKCHAIN_URL` must start with `http://`, `https://`, `ws://`, or `wss://`
- `NATIVE_TOKEN_ADDRESS` must match `^0x[a-fA-F0-9]{40}$` (if provided)
- `P2P_PORT` must be an integer in `[1, 65535]`
- `NODE_ID` must be a non-empty string of 100 characters or less
- Each entry in `INITIAL_PEERS` must start with `http://` or `https://`
- `DB_PATH`, `DATA_DIR`, and the directory of `SQLITE_DB_PATH` must be creatable

## Runtime Configuration

### Add Token Support

New ERC-20 tokens can be added at runtime via the Internal API
(see `datamgmtnode/api/internal_api.py:156`):

```bash
curl -X POST http://localhost:8080/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x6B175474E89094C44Da98b954EedeaC495271d0F",
    "abi": [/* ERC-20 ABI array */]
  }'
```

!!! note "Blockchain swap is an in-process call, not an API"
    `Node.change_blockchain(...)` exists as a Python method
    (`datamgmtnode/services/node.py:260`) but is **not** exposed via any HTTP
    route. To switch chains today, restart the node with a new
    `BLOCKCHAIN_URL` / `PRIVATE_KEY`.

## Next Steps

- [Security Best Practices](../operations/security.md) - Secure your configuration
- [Deployment Guide](../operations/deployment.md) - Production deployment
