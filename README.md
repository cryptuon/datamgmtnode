# DataMgmt Node

**[🌐 Site](https://datamgmtnode.cryptuon.com/) · [📚 Docs](https://docs.cryptuon.com/datamgmtnode/) · [🗺️ Roadmap](./ROADMAP.md) · [🔬 Cryptuon Research](https://github.com/cryptuon)**

DataMgmt Node is a decentralized enterprise data-management platform that combines **EVM-compatible blockchains**, a **Kademlia DHT peer-to-peer network**, and **end-to-end encryption** to make data sharing secure, compliant, and provably auditable. Every share, access, and compliance event is hashed and anchored on-chain, producing an **immutable, independently verifiable audit trail** — the kind of provenance that tokenized real-world assets (RWA) and regulated data now require.

Python · EVM · MIT-licensed.

## Why this matters in 2026

The 2026 enterprise-blockchain conversation has moved past "put a database on a chain." The pressure now is **verifiable provenance**: proving *where data came from, who touched it, and that it hasn't been altered* — without handing everything to a single centralized platform.

- **RWA tokenization needs a paper trail.** A tokenized bond, invoice, carbon credit, or property title is only as trustworthy as the off-chain data backing it. DataMgmt Node lets the documents, valuations, and attestations behind a token be shared under encryption while their integrity is anchored on-chain — so a token's underlying data has a tamper-evident lineage anyone can check.
- **Regulated data sharing is a compliance problem, not just a storage problem.** Healthcare, financial-services, and supply-chain data must be shared across organizational boundaries *and* leave an audit trail that survives disputes and examinations. Recording a SHA-256 hash of every compliance event on-chain turns "trust our logs" into "verify the hash."
- **Centralized audit logs can be edited by their owner.** The party that controls the log controls the truth. Anchoring event hashes to an EVM chain removes that single point of trust — logs become append-only and independently verifiable.
- **Decentralized ≠ ungoverned.** DataMgmt Node pairs a P2P data layer with encryption-at-rest, key rotation, and on-chain compliance recording, so decentralization and governance coexist.

This is deliberately *not* a hype claim. The system is Alpha-stage (see [`ROADMAP.md`](./ROADMAP.md) for the honest production path). What it demonstrates today is a working reference architecture for provenance-first data sharing.

## Features

- **EVM blockchain integration** — anchor compliance events and settle token payments on any EVM-compatible chain (Ethereum L1 or, recommended, an L2 like Base/Polygon/Arbitrum — see [`ROADMAP.md`](./ROADMAP.md)).
- **Kademlia DHT P2P network** — decentralized key-value storage with automatic peer discovery, peer-exchange, health monitoring, and re-bootstrap. No central data server.
- **End-to-end encryption** — data is encrypted with Fernet (AES-128-CBC + HMAC) before it ever enters the DHT. Encryption keys are themselves encrypted at rest with a master password via PBKDF2-HMAC-SHA256 (480,000 iterations) and support **versioned rotation**.
- **Immutable, verifiable audit trails** — every compliance event is SHA-256 hashed and written on-chain, then re-checkable via `verify_data` / `get_compliance_history`.
- **Token & payment layer** — native and custom EVM tokens for metering and paying for data transactions.
- **Persistent local storage** — LevelDB (via `plyvel`) for node data, SQLite for structured records.
- **Plugin system** — extend node behavior without forking core.
- **Multiple interfaces** — internal API, external API, a web dashboard API, and a built-in Terminal UI (`--tui`).

## Prerequisites

- Python 3.11+
- [Poetry](https://python-poetry.org/) (recommended) or pip
- An EVM RPC endpoint (Infura, Alchemy, or your own node — an L2 endpoint is recommended, see the roadmap)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/cryptuon/datamgmtnode.git
   cd datamgmtnode
   ```

2. Install dependencies with Poetry:
   ```bash
   poetry install
   ```

   > On some platforms `plyvel` (LevelDB) requires the LevelDB system library. On Debian/Ubuntu: `apt-get install libleveldb-dev`. On macOS: `brew install leveldb`.

## Configuration

Configuration is loaded from environment variables. Copy the template and edit it:

```bash
cp .env.example .env
```

Key settings in `.env`:

```bash
# Security — protects encryption keys at rest
KEY_MASTER_PASSWORD=your-strong-master-password-here

# Blockchain — an L2 RPC is recommended for production (see ROADMAP.md)
BLOCKCHAIN_TYPE=evm
BLOCKCHAIN_URL=https://mainnet.infura.io/v3/YOUR-PROJECT-ID
PRIVATE_KEY=your_private_key_here
NATIVE_TOKEN_ADDRESS=0x0000000000000000000000000000000000000000

# Storage
DB_PATH=./data/nodedb
SQLITE_DB_PATH=./data/sqlite.db

# P2P network
P2P_PORT=8000
INITIAL_PEERS=http://peer1.example.com,http://peer2.example.com

# Node identity
NODE_ID=node1
NODE_SIGNATURE=your_node_signature_here
```

See `.env.example` for the full list of options.

## Usage

Run the tests:

```bash
poetry run pytest tests/ -v
```

Start the node (server mode):

```bash
poetry run python datamgmtnode/main.py
```

On startup the node exposes:

- **Internal API:** `http://localhost:8080`
- **External API:** `http://0.0.0.0:8081`
- **Dashboard API:** `http://localhost:8082` (disable with `--no-dashboard`)
- **P2P port:** `8000` (configurable)

Launch the Terminal UI instead of server mode:

```bash
poetry run python datamgmtnode/main.py --tui
```

## API Endpoints

### Internal API

- `GET /balance/{address}` — get the token balance of an address
- `POST /transfer` — transfer tokens

### External API

- `POST /share_data` — encrypt and share data across the P2P network
- `GET /verify_data/{data_hash}` — verify the integrity of shared data
- `GET /get_compliance_history` — retrieve the on-chain compliance/audit event history

## Extending Functionality

Add new features via plugins in the `plugins/` directory. Each plugin is a Python module exposing a class that hooks into the node's plugin manager.

## Security Considerations

- Store `PRIVATE_KEY` and `KEY_MASTER_PASSWORD` in a secrets manager or HSM — never commit them. See [`ROADMAP.md`](./ROADMAP.md#cheapest-path-to-production) for key-management guidance.
- Serve all API endpoints over HTTPS in production and place them behind authentication.
- Rotate encryption keys periodically (the `KeyManager` supports versioned rotation).
- Keep dependencies patched; run a security audit before handling real regulated data.

## Roadmap & Production Path

DataMgmt Node is **Alpha**. Before it touches regulated or asset-backing data in production, read [`ROADMAP.md`](./ROADMAP.md) — it covers the vision, milestones, and a concrete **[cheapest path to production](./ROADMAP.md#cheapest-path-to-production)** (which EVM L2 to anchor on, key management, compliance controls, and DHT reliability).

## Contributing

Contributions are welcome! Please see [`CONTRIBUTING.md`](./CONTRIBUTING.md) and feel free to open an issue or Pull Request.

## License

This project is licensed under the MIT License — see the [LICENSE](LICENSE) file for details.

---

## Part of Cryptuon Research

`datamgmtnode` is one of [20 open-source blockchain-infrastructure projects](https://www.cryptuon.com/projects) from **[Cryptuon Research](https://www.cryptuon.com)** — blockchain theory, shipped as protocols.

**Related projects:** [SolanaVault](https://solanavault.cryptuon.com/) · [Switchboard](https://switchboard.cryptuon.com/) · [blockchain-compression](https://blockchain-compression.cryptuon.com/)

Docs: [docs.cryptuon.com/datamgmtnode](https://docs.cryptuon.com/datamgmtnode/) · Contact: [contact@cryptuon.com](mailto:contact@cryptuon.com)
