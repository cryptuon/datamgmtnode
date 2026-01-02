# Architecture

Technical architecture of DataMgmt Node.

## System Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                              DataMgmt Node                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                             │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         API Layer                                    │   │
│  │  ┌──────────────────────┐    ┌──────────────────────┐              │   │
│  │  │    Internal API      │    │    External API      │              │   │
│  │  │    (Port 8080)       │    │    (Port 8081)       │              │   │
│  │  │  • Health check      │    │  • Share data        │              │   │
│  │  │  • Token balance     │    │  • Get data          │              │   │
│  │  │  • Token transfer    │    │  • Verify compliance │              │   │
│  │  │  • Token management  │    │  • Network stats     │              │   │
│  │  └──────────────────────┘    └──────────────────────┘              │   │
│  │                    ↓                      ↓                         │   │
│  │  ┌──────────────────────────────────────────────────────────────┐  │   │
│  │  │                    Middleware Layer                           │  │   │
│  │  │  • Rate Limiting  • Error Handling  • Request Validation     │  │   │
│  │  └──────────────────────────────────────────────────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                         Service Layer                                │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │
│  │  │   Data     │ │   Token    │ │  Payment   │ │   Compliance   │   │   │
│  │  │  Manager   │ │  Manager   │ │ Processor  │ │    Manager     │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │   │
│  │  ┌────────────┐ ┌────────────┐ ┌────────────┐ ┌────────────────┐   │   │
│  │  │    Key     │ │   Auth     │ │  Plugin    │ │                │   │   │
│  │  │  Manager   │ │  Module    │ │  Manager   │ │                │   │   │
│  │  └────────────┘ └────────────┘ └────────────┘ └────────────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                     ↓                                       │
│  ┌─────────────────────────────────────────────────────────────────────┐   │
│  │                        Infrastructure Layer                          │   │
│  │  ┌────────────────┐  ┌────────────────┐  ┌────────────────────┐    │   │
│  │  │   P2P Network  │  │   Blockchain   │  │      Storage       │    │   │
│  │  │   (Kademlia)   │  │   Interface    │  │  (LevelDB/RocksDB) │    │   │
│  │  └────────────────┘  └────────────────┘  └────────────────────┘    │   │
│  └─────────────────────────────────────────────────────────────────────┘   │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Component Details

### API Layer

#### Internal API (`api/internal_api.py`)

Handles node management operations:

```python
class InternalAPI:
    """Internal API for node management operations (port 8080)."""

    def __init__(self, node):
        self.node = node
        self.rate_limiter = create_internal_rate_limiter()

    async def start(self):
        app = aiohttp.web.Application(middlewares=[...])
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/balance/{address}', self.get_balance)
        app.router.add_post('/transfer', self.transfer)
        app.router.add_get('/tokens', self.list_tokens)
        app.router.add_post('/tokens', self.add_token)
```

#### External API (`api/external_api.py`)

Handles data sharing operations:

```python
class ExternalAPI:
    """External API for data sharing operations (port 8081)."""

    async def start(self):
        app = aiohttp.web.Application(middlewares=[...])
        app.router.add_get('/health', self.health_check)
        app.router.add_post('/share_data', self.share_data)
        app.router.add_get('/data/{data_hash}', self.get_data)
        app.router.add_get('/verify_data/{data_hash}', self.verify_data)
        app.router.add_get('/compliance_history', self.get_compliance_history)
        app.router.add_get('/network/stats', self.get_network_stats)
        app.router.add_get('/network/peers', self.get_peers)
```

### Service Layer

#### DataManager (`services/data_manager.py`)

Local data storage using LevelDB or RocksDB:

```python
class DataManager:
    def __init__(self, db_path):
        self.db = self._init_database()  # LevelDB or RocksDB

    def store_data(self, key, value): ...
    def get_data(self, key): ...
    def delete_data(self, key): ...
```

#### TokenManager (`services/token_manager.py`)

ERC-20 token management:

```python
class TokenManager:
    def __init__(self, blockchain_interface, native_token_address):
        self.blockchain = blockchain_interface
        self.supported_tokens = {native_token_address}

    def get_balance(self, address, token): ...
    def transfer_tokens(self, from_addr, to_addr, amount, token): ...
    def add_supported_token(self, address, abi): ...
```

#### KeyManager (`services/key_manager.py`)

Secure encryption key management:

```python
class KeyManager:
    def __init__(self, keys_dir, master_password=None):
        self._master_password = master_password or os.getenv('KEY_MASTER_PASSWORD')
        self._keys: dict[int, bytes] = {}

    def initialize(self) -> Fernet: ...
    def rotate_key(self) -> int: ...
    def get_cipher(self, version: int) -> Fernet: ...
```

#### ComplianceManager (`services/compliance_manager.py`)

Blockchain compliance recording:

```python
class ComplianceManager:
    def record_compliance_event(self, event_type, event_data): ...
    def verify_compliance(self, event_type, event_hash): ...
    def get_compliance_history(self, filters=None): ...
```

### Infrastructure Layer

#### P2PNetwork (`network/p2p_network.py`)

Kademlia-based peer-to-peer network:

```python
class P2PNetwork:
    def __init__(self, node, port, initial_peers, data_dir):
        self.dht_server = None
        self.known_peers: Dict[str, PeerInfo] = {}

    async def start(self): ...
    async def stop(self): ...
    async def send_data(self, data_hash, data): ...
    async def get_data(self, data_hash): ...
```

#### BlockchainInterface (`blockchain/evm_blockchain_interface.py`)

EVM blockchain interaction:

```python
class EVMBlockchainInterface:
    def __init__(self, rpc_url, private_key):
        self.w3 = Web3(Web3.HTTPProvider(rpc_url))
        self.account = Account.from_key(private_key)

    def connect(self): ...
    def send_transaction(self, tx_data): ...
    def call_contract(self, contract_address, abi, function, *args): ...
```

## Data Flow

### Share Data Flow

```
Client                 External API           Node Core              P2P Network
   │                        │                     │                       │
   │── POST /share_data ──>│                     │                       │
   │                        │── validate ──────>│                       │
   │                        │                     │── encrypt ─────────>│
   │                        │                     │                       │
   │                        │                     │── store locally ───>│
   │                        │                     │                       │
   │                        │                     │── distribute ──────>│
   │                        │                     │                       │
   │                        │                     │── record compliance ─>│
   │                        │                     │                       │
   │<── tx_hash ───────────│<── response ───────│                       │
```

### Retrieve Data Flow

```
Client                 External API           Node Core              P2P Network
   │                        │                     │                       │
   │── GET /data/{hash} ──>│                     │                       │
   │                        │── validate ──────>│                       │
   │                        │                     │── check local ─────>│
   │                        │                     │                       │
   │                        │                     │   [if not found]     │
   │                        │                     │── query DHT ───────>│
   │                        │                     │                       │
   │                        │                     │<── data ────────────│
   │                        │                     │                       │
   │<── data ──────────────│<── response ───────│                       │
```

## Configuration

### NodeConfig

```python
class NodeConfig:
    blockchain_type: str      # 'evm'
    blockchain_url: str       # RPC endpoint
    private_key: str          # Signing key
    native_token_address: str # Token contract
    db_path: str              # LevelDB path
    sqlite_db_path: str       # SQLite path
    p2p_port: int             # P2P listening port
    plugin_dir: str           # Plugin directory
    node_id: str              # Node identifier
    node_signature: str       # Node signature
    initial_peers: list       # Bootstrap peers
    data_dir: str             # Data directory

    def validate(self): ...   # Validate configuration
```

### Configuration Validation

```python
def validate(self):
    errors = []

    if self.blockchain_type not in ['evm']:
        errors.append("Unsupported blockchain_type")

    if not self.blockchain_url:
        errors.append("blockchain_url is required")

    if not (1 <= self.p2p_port <= 65535):
        errors.append("p2p_port out of range")

    if errors:
        raise ConfigurationError(errors)
```

## Error Handling

### Middleware Pattern

```python
@aiohttp.web.middleware
async def error_middleware(self, request, handler):
    try:
        return await handler(request)
    except ValidationError as e:
        return json_response({'error': e.message}, status=422)
    except aiohttp.web.HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Error: {e}")
        return json_response({'error': 'Internal error'}, status=500)
```

### Validation Errors

```python
class ValidationError(Exception):
    def __init__(self, message: str, field: str = None):
        self.message = message
        self.field = field
```

## Plugin System

### Plugin Interface

```python
class BasePlugin:
    def __init__(self, node):
        self.node = node

    def initialize(self):
        """Called when plugin is loaded."""
        pass

    def shutdown(self):
        """Called when node shuts down."""
        pass
```

### Plugin Loading

```python
class PluginManager:
    def load_plugins(self):
        for filename in os.listdir(self.plugin_dir):
            if filename.endswith('.py'):
                module = __import__(f'plugins.{module_name}')
                plugin_class = getattr(module, f'{name}Plugin')
                plugin = plugin_class(self.node)
                plugin.initialize()
```

## Testing

### Test Structure

```
tests/
├── test_authorisation.py
├── test_compliance_manager.py
├── test_data_manager.py
├── test_p2p_network.py
├── test_payment_processor.py
├── test_token_manager.py
├── test_api_validation.py
├── test_rate_limiter.py
├── test_config.py
└── test_key_manager.py
```

### Test Patterns

```python
class TestDataManager:
    @pytest.fixture
    def temp_db_path(self, tmp_path):
        return str(tmp_path / "testdb")

    def test_store_and_get_data(self, temp_db_path):
        dm = DataManager(temp_db_path)
        dm.store_data("key1", "value1")
        assert dm.get_data("key1") == "value1"
```

## Next Steps

- [Contributing Guide](contributing.md) - How to contribute
- [Testing Guide](testing.md) - Running tests
