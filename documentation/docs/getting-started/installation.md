# Installation

This guide covers installing DataMgmt Node on your system.

## Prerequisites

Before installing DataMgmt Node, ensure you have:

- **Python 3.10+** (3.12 recommended)
- **Poetry** for dependency management
- **LevelDB** or **RocksDB** for data storage
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
git clone https://github.com/example/datamgmtnode.git
cd datamgmtnode

# Install dependencies
poetry install

# Verify installation
poetry run python -c "from datamgmtnode.services.node import Node; print('Installation successful!')"
```

### Using pip (Coming Soon)

```bash
pip install datamgmtnode
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

You should see all tests passing:

```
========================= 173 passed in 4.76s =========================
```

## Build Web Dashboard (Optional)

If you want to use the web-based dashboard, build it after installation:

```bash
# Build the Vue.js dashboard
python scripts/build_dashboard.py
```

This compiles the frontend and copies it to `datamgmtnode/dashboard/static/`. The dashboard will then be served automatically when you start the node.

See [Web Dashboard](../user-guide/web-dashboard.md) for more details.

## Next Steps

- [Quick Start Guide](quickstart.md) - Share your first data
- [Configuration Reference](configuration.md) - Full configuration options
- [Web Dashboard](../user-guide/web-dashboard.md) - Browser-based interface
- [Terminal UI](../user-guide/terminal-ui.md) - Command-line interface
- [Security Best Practices](../operations/security.md) - Secure your node
