#!/bin/bash
set -e

echo "=========================================="
echo "  DataMgmt Node - Starting Services"
echo "=========================================="

# Create required directories
mkdir -p /app/data /var/log/nginx /var/log/supervisor

# Set default environment variables if not provided
export BLOCKCHAIN_TYPE=${BLOCKCHAIN_TYPE:-evm}
export BLOCKCHAIN_URL=${BLOCKCHAIN_URL:-https://sepolia.infura.io/v3/demo}
export DB_PATH=${DB_PATH:-/app/data/nodedb}
export SQLITE_DB_PATH=${SQLITE_DB_PATH:-/app/data/sqlite.db}
export P2P_PORT=${P2P_PORT:-8000}
export PLUGIN_DIR=${PLUGIN_DIR:-/app/plugins}
export NODE_ID=${NODE_ID:-demo-node}
export DATA_DIR=${DATA_DIR:-/app/data}

# API ports (internal use)
export INTERNAL_API_HOST=${INTERNAL_API_HOST:-localhost}
export INTERNAL_API_PORT=${INTERNAL_API_PORT:-8080}
export EXTERNAL_API_HOST=${EXTERNAL_API_HOST:-0.0.0.0}
export EXTERNAL_API_PORT=${EXTERNAL_API_PORT:-8081}

# Generate a random node signature if not provided
if [ -z "$NODE_SIGNATURE" ]; then
    export NODE_SIGNATURE=$(python -c "import secrets; print(secrets.token_hex(32))")
fi

# Check for required secrets
if [ -z "$KEY_MASTER_PASSWORD" ]; then
    echo "WARNING: KEY_MASTER_PASSWORD not set, using generated value"
    export KEY_MASTER_PASSWORD=$(python -c "import secrets; print(secrets.token_urlsafe(32))")
fi

if [ -z "$PRIVATE_KEY" ]; then
    echo "WARNING: PRIVATE_KEY not set - using demo key for testnet"
    echo "Set PRIVATE_KEY environment variable for production use"
    # Demo-only private key for testnet (no real funds)
    export PRIVATE_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
fi

echo ""
echo "Configuration:"
echo "  - Blockchain: $BLOCKCHAIN_TYPE"
echo "  - Network: $BLOCKCHAIN_URL"
echo "  - Node ID: $NODE_ID"
echo "  - P2P Port: $P2P_PORT"
echo ""
echo "Endpoints (via nginx on port 80):"
echo "  - Website:    http://localhost/"
echo "  - API:        http://localhost/api/"
echo "  - WebSocket:  ws://localhost/ws"
echo "  - Health:     http://localhost/health"
echo ""
echo "=========================================="

# Execute the main command
exec "$@"
