# Installation

This guide covers installing DataMgmt Node on your system.

## Prerequisites

Before installing DataMgmt Node, ensure you have:

- **Python 3.11+** (declared as `python = "^3.11"` in `pyproject.toml`)
- **Poetry** for dependency management
- **LevelDB** (RocksDB optional — `DataManager` tries RocksDB first, falls back to LevelDB / Plyvel; see `datamgmtnode/services/data_manager.py:12`)
- Access to an **EVM-compatible blockchain** (Ethereum, Polygon, etc.)

**Optional (for web dashboard):**

- **Node.js 18+** and npm (required to build the web dashboard)

## Install Dependencies

### Ubuntu/Debian

```bash
# Install system dependencies
sudo apt update
sudo apt install -y python3 python3-pip libleveldb-dev

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Optional: Install Node.js for web dashboard
curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
sudo apt install -y nodejs
```

### macOS

```bash
# Using Homebrew
brew install python@3.12 leveldb

# Install Poetry
curl -sSL https://install.python-poetry.org | python3 -

# Optional: Install Node.js for web dashboard
brew install node
```

### Windows

```powershell
# Install Python from python.org
# Install Poetry
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | python -

# Optional: Install Node.js for web dashboard from https://nodejs.org/
```

## Install DataMgmt Node

### From Source

```bash
# Clone the repository
git clone https://github.com/cryptuon/datamgmtnode.git
cd datamgmtnode

# Install dependencies
poetry install

# Verify installation
poetry run python -c "from datamgmtnode.services.node import Node; print('Installation successful!')"
```

### Using Docker

The repo ships a multi-stage `Dockerfile` that builds the Vue website and the
Python node together, served via nginx on port 80. See
[Deployment](../operations/deployment.md) for full details.

```bash
docker build -t datamgmtnode .
docker run -p 80:80 \
  -e KEY_MASTER_PASSWORD="strong-secret" \
  -e BLOCKCHAIN_URL="https://mainnet.infura.io/v3/YOUR-PROJECT-ID" \
  -e PRIVATE_KEY="0x..." \
  datamgmtnode
```

## Configuration

1. Copy the example environment file:

```bash
cp .env.example .env
```

2. Edit `.env` with your configuration:

```bash
# Required settings
BLOCKCHAIN_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
PRIVATE_KEY=your_private_key_here
KEY_MASTER_PASSWORD=your-strong-master-password

# Optional settings
NODE_ID=my-node-1
P2P_PORT=8000
```

!!! warning "Security Notice"
    Never commit your `.env` file or share your private key. The `KEY_MASTER_PASSWORD` is used to encrypt your encryption keys at rest.

## Verify Installation

Run the test suite to verify everything is working:

```bash
poetry run pytest tests/ -v
```

There are 173 tests across the suite (counted from `tests/test_*.py`).

## Build Web Dashboard (Optional)

If you want to use the web-based dashboard, build it after installation:

```bash
# Build the Vue.js dashboard
python scripts/build_dashboard.py
```

This compiles the Vue 3 + Vite frontend (see `web/package.json`) and copies the `dist/` output to `datamgmtnode/dashboard/static/` (see `scripts/build_dashboard.py:23`). The Dashboard API will then serve it automatically on port 8082 when you start the node.

See [Web Dashboard](../user-guide/web-dashboard.md) for more details.

## Next Steps

- [Quick Start Guide](quickstart.md) - Share your first data
- [Configuration Reference](configuration.md) - Full configuration options
- [Web Dashboard](../user-guide/web-dashboard.md) - Browser-based interface
- [Terminal UI](../user-guide/terminal-ui.md) - Command-line interface
- [Security Best Practices](../operations/security.md) - Secure your node
