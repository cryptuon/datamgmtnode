# DataMgmt Node

This project implements a decentralized system for enterprise data management and sharing, leveraging blockchain technology, peer-to-peer networking, and flexible data storage solutions.

## Features

- Blockchain integration with support for EVM-compatible chains
- Peer-to-peer data sharing using the Gun P2P network
- Flexible data storage with support for both RocksDB and LevelDB
- Token management for native and custom tokens
- Payment processing for data transactions
- Compliance management and event logging on the blockchain
- Plugin system for extensibility
- Internal and external APIs for system interaction

## Prerequisites

- Python 3.7+
- pip (Python package manager)

## Installation

1. Clone the repository:
   ```
   git clone https://github.com/your-repo/decentralized-data-system.git
   cd decentralized-data-system
   ```

2. Install the required dependencies:
   ```
   pip install web3 pygundb cryptography aiohttp
   ```

3. Install either RocksDB or LevelDB:
   - For RocksDB:
     ```
     pip install python-rocksdb
     ```
   - For LevelDB:
     ```
     pip install plyvel
     ```

## Configuration

Create a configuration file `config.py` with the following content:

```python
from node import NodeConfig

config = NodeConfig(
    blockchain_type='evm',
    blockchain_url='https://mainnet.infura.io/v3/YOUR-PROJECT-ID',
    private_key='your_private_key_here',
    native_token_address='0x...',
    db_path='./nodedb',
    sqlite_db_path='./sqlite.db',
    p2p_port=8000,
    plugin_dir='./plugins',
    node_id='node1',
    node_signature='signature_here',
    initial_peers=['http://peer1.example.com', 'http://peer2.example.com']
)
```

Replace the placeholder values with your actual configuration.

## Usage

1. Start the node:
   ```
   python main.py
   ```

2. Interact with the node using the internal and external APIs:
   - Internal API: `http://localhost:8080`
   - External API: `http://localhost:8081`

## API Endpoints

### Internal API

- GET `/balance/{address}`: Get the balance of an address
- POST `/transfer`: Transfer tokens

### External API

- POST `/share_data`: Share data with other nodes
- GET `/verify_data/{data_hash}`: Verify shared data
- GET `/get_compliance_history`: Retrieve compliance event history

## Extending Functionality

To add new features or customize behavior, you can create plugins in the `plugins` directory. Each plugin should be a Python module with a class that inherits from a base plugin class (to be implemented).

## Security Considerations

- Ensure that your private keys and sensitive data are stored securely.
- Use HTTPS for all API endpoints in production.
- Regularly update dependencies to patch any security vulnerabilities.
- Implement proper access control and authentication mechanisms for your APIs.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.