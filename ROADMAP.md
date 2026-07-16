# DataMgmt Node — Roadmap

## Vision

DataMgmt Node aims to be the **provenance layer for regulated and asset-backing data**: a decentralized way for organizations to share sensitive data under encryption while every access and compliance event leaves an **immutable, independently verifiable audit trail** anchored on an EVM chain.

The 2026 opportunity is concrete. **RWA tokenization** is pushing enormous volumes of off-chain data (valuations, attestations, legal documents, invoices) toward on-chain assets that are only as trustworthy as that data's lineage. **Regulated data sharing** in healthcare, finance, and supply chains needs audit trails that survive audits and disputes. Both problems reduce to the same primitive: *prove data integrity and history without trusting a single centralized platform*. That is what DataMgmt Node is built to demonstrate.

We are honest about stage: the platform is **Alpha**. This roadmap is the path from working reference architecture to something you could responsibly run against real regulated data.

## Milestones

### M1 — Verifiable core (largely in place)
- Kademlia DHT P2P data layer with peer discovery, health monitoring, and re-bootstrap ✅
- Fernet end-to-end encryption with PBKDF2-protected, versioned keys ✅
- On-chain compliance event recording (SHA-256 hash anchored on EVM) ✅
- Token + payment layer for metering data transactions ✅
- Test suite (74 tests) ✅

### M2 — Provenance you can trust
- Structured, queryable compliance/audit index (move beyond linear block scanning in `compliance_manager`)
- Signed data manifests: bind each shared payload to node identity + timestamp + content hash
- Merkle batching of compliance events to cut on-chain cost and enable efficient inclusion proofs
- Access-grant records (who was granted/revoked access to what, on-chain)

### M3 — Enterprise & compliance readiness
- Pluggable access control (RBAC/ABAC) and retention policies
- Optional KYC/allowlist gating for regulated data pools
- Key management via external KMS/HSM instead of local master password
- Structured logging + Prometheus metrics + health/SLA dashboards

### M4 — RWA integrations
- Reference adapters that link a shared data manifest to an RWA token's metadata
- Attestation flow: third-party signer vouches for underlying data, recorded on-chain
- Data-availability guarantees (replication factor SLAs) for token-backing documents

---

## Cheapest path to production

You do **not** need Ethereum L1 to run DataMgmt Node in production, and you shouldn't start there. The workload here is *many small compliance-event transactions* (one hashed event per share/access). On L1 mainnet, each of those is dollars of gas; the pattern is economically absurd at any real volume. **Anchor on the cheapest viable EVM L2 instead.**

### 1. Anchor on a low-cost EVM L2

Because the code is already EVM-generic (just point `BLOCKCHAIN_URL` at a different RPC), migrating is a config change, not a rewrite.

| Chain | Typical cost per compliance-event tx | Why it fits | Tradeoff |
|-------|--------------------------------------|-------------|----------|
| **Base** | fractions of a cent | Low fees, strong tooling, backed by a major exchange; good default for enterprise pilots | Sequencer is currently centralized |
| **Polygon PoS** | ~a cent or less | Mature, huge ecosystem, easy RPC availability | Its own validator-set trust assumptions |
| **Arbitrum One** | fractions of a cent | Largest L2 by activity, robust fraud-proof security model | Marginally higher fees than Base at times |
| Ethereum L1 | dollars | Maximum decentralization/finality | Far too expensive for per-event anchoring |

**Recommendation:** start on **Base** for a pilot (cheapest + simplest operationally), keep **Polygon** and **Arbitrum** as drop-in alternatives, and reserve **Ethereum L1** only for periodic Merkle-root checkpointing if a customer demands L1-grade finality. Batch events into Merkle roots (M2) so you write one root instead of one tx per event — this cuts anchoring cost by another order of magnitude.

### 2. Production-viability checklist

Anchoring cheaply is necessary but not sufficient. Before real regulated or asset-backing data:

- **Security audit** — independent review of the encryption path, key handling, blockchain interface, and API authorization. No production regulated data before this.
- **Key management / HSM** — move `PRIVATE_KEY` and `KEY_MASTER_PASSWORD` out of `.env` into a managed KMS/HSM (AWS KMS, GCP KMS, HashiCorp Vault, or a hardware HSM). Enforce key rotation.
- **Compliance controls** — access control (RBAC/ABAC), data retention + deletion policies, and KYC/allowlist gating where the jurisdiction or asset class requires it. Map controls to the relevant regime (HIPAA, GDPR, SOC 2, MiCA/RWA rules).
- **DHT reliability / replication** — configure and monitor replication factor so no shared payload lives on a single node; alert on under-replication; validate re-bootstrap under partition.
- **Monitoring & observability** — structured logging, Prometheus metrics, uptime/latency SLAs on the P2P and API layers, and alerting on anchoring failures (a dropped compliance write is a compliance gap).

### 3. Rough cost posture for a pilot

- One low-cost L2 RPC endpoint (managed tier): tens of dollars/month.
- 3–5 small P2P nodes (commodity VMs) for replication: low hundreds of dollars/month.
- Per-event anchoring on an L2 with Merkle batching: cents/day at pilot volume.

The dominant cost is engineering the compliance and audit posture — not chain fees. Choosing an L2 up front keeps chain fees a rounding error so the budget goes where the risk actually is.

---

# Development History

_The section below is the historical build/fix log for the reference implementation. It is retained for accuracy and is not part of the forward roadmap above._

## Status: All Phases Complete

All critical fixes, bug fixes, testing, P2P implementation, and configuration work has been completed.

---

## Completed Work

### Phase 1: Critical Fixes (All Fixed)

| Issue | File | Status |
|-------|------|--------|
| Missing 8 imports | `services/node.py` | Fixed |
| Missing aiohttp import | `api/internal_api.py` | Fixed |
| Missing aiohttp import | `api/external_api.py` | Fixed |
| Missing hashlib import | `services/compliance_manager.py` | Fixed |
| Missing os import | `services/plugin_manager.py` | Fixed |
| Wrong cryptography API | `services/authorisation.py` | Fixed |
| Missing Account import | `blockchain/evm_blockchain_interface.py` | Fixed |
| Unused imports | `blockchain/blockchain_interface.py` | Cleaned up |

### Phase 2: Dependencies (Complete)

Updated `pyproject.toml` with:
- `aiohttp` - HTTP APIs
- `kademlia` - P2P DHT networking (replaced non-existent pygundb)
- `plyvel` - LevelDB storage
- `python-dotenv` - Environment configuration
- `pytest`, `pytest-asyncio`, `pytest-cov` - Testing (dev dependencies)

### Phase 3: Bug Fixes (All Fixed)

| Issue | File | Status |
|-------|------|--------|
| Missing `await` | `api/external_api.py:21` | Fixed |
| Bare `except` clause | `services/authorisation.py` | Fixed with proper exception handling |
| tx_hash vs receipt inconsistency | `blockchain/evm_blockchain_interface.py` | Fixed - `send_transaction` returns hash, added `wait_for_receipt` |
| Token transaction bug | `services/token_manager.py` | Fixed - properly builds transactions for token operations |
| Placeholder methods | `blockchain/evm_blockchain_interface.py` | Implemented with file-based contract artifact loading |

### Phase 4: Testing (Complete)

Created comprehensive test suite (58 tests):
- `tests/conftest.py` - Shared fixtures and mocks
- `tests/test_data_manager.py` - DataManager unit tests (8 tests)
- `tests/test_token_manager.py` - TokenManager unit tests (10 tests)
- `tests/test_payment_processor.py` - PaymentProcessor unit tests (7 tests)
- `tests/test_compliance_manager.py` - ComplianceManager unit tests (7 tests)
- `tests/test_authorisation.py` - AuthorizationModule unit tests (8 tests)
- `tests/test_p2p_network.py` - P2PNetwork unit tests (34 tests)

### Phase 6: P2P Network Implementation (Complete)

Replaced non-existent `pygundb` with `kademlia` DHT:
- **Kademlia DHT** provides decentralized key-value storage
- Full rewrite of `network/p2p_network.py`

**Core Features:**
- `start()`/`stop()` - Server lifecycle management
- `send_data()` - Encrypt and store data in DHT
- `get_data()` - Retrieve and decrypt data from DHT
- `connect_to_peer()` - Dynamic peer connection
- `broadcast_data()` - Replicate data across network

**Peer Discovery & Management:**
- **Persistent peer storage** - Saves/loads known peers to `data/known_peers.json`
- **Automatic re-bootstrap** - Reconnects when peer count drops below minimum
- **Peer exchange protocol** - Nodes share peer lists via DHT
- **Health monitoring** - Tracks latency, success rate, prunes dead peers

**New APIs:**
- `get_connected_peers()` - List all peers with health info
- `get_healthy_peers()` - List only healthy peers
- `get_network_stats()` - Network statistics (total/healthy peers, avg latency)

**Background Tasks (automatic):**
- Health check loop (every 60s)
- Peer exchange loop (every 120s)
- Re-bootstrap loop (every 300s if < 3 peers)

### Phase 5: Configuration (Complete)

- Created `.env.example` with all configuration options
- Updated `main.py` to load configuration from environment variables
- Created directory structure:
  - `contracts/` - Contract artifacts (includes sample ERC20Token.json)
  - `data/` - Database storage
  - `plugins/` - Plugin directory

---

## How to Run

### 1. Install Dependencies
```bash
poetry install
```

### 2. Configure Environment
```bash
cp .env.example .env
# Edit .env with your configuration
```

### 3. Run Tests
```bash
poetry run pytest tests/ -v
```

### 4. Start the Node
```bash
poetry run python datamgmtnode/main.py
```

---

## Project Structure (Updated)

```
datamgmtnode/
├── contracts/                  # Contract artifacts (NEW)
│   └── ERC20Token.json
├── data/                       # Database storage (NEW)
├── datamgmtnode/
│   ├── api/
│   │   ├── external_api.py    # External API (port 8081)
│   │   └── internal_api.py    # Internal API (port 8080)
│   ├── blockchain/
│   │   ├── blockchain_interface.py
│   │   └── evm_blockchain_interface.py
│   ├── network/
│   │   └── p2p_network.py
│   ├── services/
│   │   ├── authorisation.py
│   │   ├── compliance_manager.py
│   │   ├── data_manager.py
│   │   ├── node.py
│   │   ├── payment_processor.py
│   │   ├── plugin_manager.py
│   │   └── token_manager.py
│   └── main.py
├── plugins/                    # Plugin directory (NEW)
├── tests/                      # Test suite (NEW)
│   ├── conftest.py
│   ├── test_authorisation.py
│   ├── test_compliance_manager.py
│   ├── test_data_manager.py
│   ├── test_payment_processor.py
│   └── test_token_manager.py
├── .env.example               # Environment template (NEW)
├── pyproject.toml             # Updated dependencies
└── README.md
```

---

## Future Enhancements (Optional)

These are suggestions for future development:

1. **Integration Tests** - Test full node workflow end-to-end
2. **API Documentation** - Add OpenAPI/Swagger specs for the APIs
3. **Logging** - Add structured logging with configurable levels
4. **Metrics** - Add Prometheus metrics for monitoring
5. **Docker** - Add Dockerfile and docker-compose for containerization
6. **CI/CD** - Add GitHub Actions for automated testing
7. **Type Hints** - Add comprehensive type annotations
8. **Error Handling** - Add custom exception classes

---

## Summary

| Category | Items | Status |
|----------|-------|--------|
| Missing imports | 8 | All fixed |
| Missing dependencies | 5 | All added |
| Runtime bugs | 5 | All fixed |
| P2P network | 1 | Fully rewritten with kademlia + discovery |
| Test files | 7 | Created (74 tests) |
| Config files | 2 | Created |

**Total files modified:** 14
**Total files created:** 11
**Total tests:** 74 (all passing)
