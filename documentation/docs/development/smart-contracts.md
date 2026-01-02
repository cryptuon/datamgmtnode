# Smart Contract Development

DataMgmt Node integrates with EVM-compatible blockchains for token management and compliance recording. This guide covers deploying and interacting with smart contracts.

## Overview

The node uses smart contracts for:

- **Token Management** - ERC-20 token transfers and balances
- **Compliance Recording** - Immutable audit trail on-chain
- **Payment Processing** - Token-based payments for data sharing

## Contract Artifacts

Contract artifacts are stored in the `contracts/` directory as JSON files:

```
contracts/
├── ERC20Token.json      # Standard ERC-20 token
└── deployed_contracts.json  # Mapping of deployed addresses
```

### Artifact Format

Each contract artifact contains:

```json
{
  "contractName": "ERC20Token",
  "abi": [...],
  "bytecode": "0x..."
}
```

| Field | Description |
|-------|-------------|
| `contractName` | Human-readable contract name |
| `abi` | Application Binary Interface (function definitions) |
| `bytecode` | Compiled contract bytecode for deployment |

## ERC-20 Token Contract

The included ERC-20 token contract supports:

### Functions

| Function | Description |
|----------|-------------|
| `constructor(name, symbol, initialSupply)` | Deploy with name, symbol, and initial supply |
| `balanceOf(address)` | Get token balance for an address |
| `transfer(to, amount)` | Transfer tokens to another address |
| `mint(to, amount)` | Mint new tokens (owner only) |
| `approve(spender, amount)` | Approve spending allowance |
| `transferFrom(from, to, amount)` | Transfer on behalf of another |
| `allowance(owner, spender)` | Check spending allowance |
| `name()` | Get token name |
| `symbol()` | Get token symbol |
| `decimals()` | Get decimal places (18) |
| `totalSupply()` | Get total token supply |

## Deploying Contracts

### Using the Blockchain Interface

```python
from blockchain.evm_blockchain_interface import EVMBlockchainInterface

# Initialize blockchain interface
blockchain = EVMBlockchainInterface(
    network_url="https://polygon-rpc.com",
    private_key="0x...",
    contracts_dir="./contracts"
)
blockchain.connect()

# Deploy ERC-20 token
contract = blockchain.deploy_contract(
    "ERC20Token",
    args=["DataToken", "DATA", 1000000 * 10**18]  # 1M tokens
)

print(f"Contract deployed at: {contract.address}")
```

### Constructor Arguments

For the ERC-20 token:

| Argument | Type | Description |
|----------|------|-------------|
| `name` | string | Token name (e.g., "DataToken") |
| `symbol` | string | Token symbol (e.g., "DATA") |
| `initialSupply` | uint256 | Initial supply in wei (multiply by 10^18) |

### Tracking Deployed Contracts

Create a mapping file to track deployments:

```json
// contracts/deployed_contracts.json
{
  "0x1234567890abcdef1234567890abcdef12345678": "ERC20Token",
  "0xabcdef1234567890abcdef1234567890abcdef12": "ComplianceLog"
}
```

This allows the node to look up ABIs for deployed contracts.

## Interacting with Contracts

### Reading Contract State

```python
# Get token balance
balance = blockchain.call_contract_function(
    contract_address="0x1234...",
    function_name="balanceOf",
    args=["0xabcd..."]
)

print(f"Balance: {balance / 10**18} tokens")
```

### Writing to Contracts

```python
# Build transaction
contract = blockchain.w3.eth.contract(
    address="0x1234...",
    abi=abi
)

# Transfer tokens
tx = contract.functions.transfer(
    "0xabcd...",  # recipient
    100 * 10**18  # amount
).build_transaction({
    'from': blockchain.account.address,
    'nonce': blockchain.w3.eth.get_transaction_count(blockchain.account.address)
})

# Send transaction
tx_hash = blockchain.send_transaction(tx)
receipt = blockchain.wait_for_receipt(tx_hash)

print(f"Transaction: {tx_hash}")
print(f"Status: {'Success' if receipt.status == 1 else 'Failed'}")
```

## Using the Token Manager

The Token Manager provides a higher-level interface:

### Adding Token Support

```python
# Via API
curl -X POST http://localhost:8080/tokens \
  -H "Content-Type: application/json" \
  -d '{
    "address": "0x1234567890abcdef1234567890abcdef12345678",
    "abi": [...]
  }'
```

### Checking Balances

```python
# Get balance through token manager
balance = node.token_manager.get_balance(
    address="0xabcd...",
    token_address="0x1234..."
)
```

### Transferring Tokens

```python
# Through payment processor
success, tx_hash = node.payment_processor.process_payment(
    from_address="0xabcd...",
    to_address="0xefgh...",
    amount=100 * 10**18,
    token_address="0x1234..."
)
```

## Custom Contracts

### Creating Contract Artifacts

1. **Compile your contract** using Solidity compiler or Hardhat/Foundry

2. **Create artifact file**:

```json
// contracts/MyContract.json
{
  "contractName": "MyContract",
  "abi": [
    {
      "inputs": [],
      "name": "myFunction",
      "outputs": [{"type": "uint256"}],
      "stateMutability": "view",
      "type": "function"
    }
  ],
  "bytecode": "0x608060405234801..."
}
```

3. **Deploy using the blockchain interface**:

```python
contract = blockchain.deploy_contract("MyContract", args=[])
```

### Compiling Solidity

Using `solc`:

```bash
# Install solc
pip install py-solc-x

# Compile
solc --abi --bin MyContract.sol -o build/
```

Using Hardhat:

```bash
npx hardhat compile
# Artifacts in artifacts/contracts/
```

### ABI Format

The ABI describes contract functions:

```json
{
  "inputs": [
    {"name": "param1", "type": "address"},
    {"name": "param2", "type": "uint256"}
  ],
  "name": "functionName",
  "outputs": [
    {"name": "", "type": "bool"}
  ],
  "stateMutability": "nonpayable",
  "type": "function"
}
```

| Field | Description |
|-------|-------------|
| `inputs` | Function parameters |
| `name` | Function name |
| `outputs` | Return values |
| `stateMutability` | `view`, `pure`, `nonpayable`, `payable` |
| `type` | `function`, `constructor`, `event` |

## Compliance Recording

The node records compliance events on-chain:

### How It Works

1. Data operation occurs (share, transfer)
2. Event data is hashed
3. Hash is recorded in a transaction to the zero address
4. Transaction hash serves as proof

### Recording Events

```python
# Record compliance event
tx_hash = node.compliance_manager.record_compliance_event(
    event_type='data_share',
    event_data={
        'data_hash': 'abc123...',
        'recipient': '0xabcd...',
        'timestamp': 1705312200
    }
)
```

### Verifying Compliance

```python
# Verify event exists on chain
is_verified = node.compliance_manager.verify_compliance(
    event_type='data_share',
    event_hash='abc123...'
)
```

## Network Configuration

### Supported Networks

| Network | RPC URL | Chain ID |
|---------|---------|----------|
| Ethereum Mainnet | `https://mainnet.infura.io/v3/KEY` | 1 |
| Polygon | `https://polygon-rpc.com` | 137 |
| Arbitrum | `https://arb1.arbitrum.io/rpc` | 42161 |
| Optimism | `https://mainnet.optimism.io` | 10 |
| Local (Ganache) | `http://localhost:8545` | 1337 |

### Switching Networks

```python
# At runtime
node.change_blockchain(
    new_blockchain_type='evm',
    new_blockchain_url='https://polygon-rpc.com',
    new_private_key='0x...'
)
```

Or via configuration:

```bash
# .env
BLOCKCHAIN_URL=https://polygon-rpc.com
```

## Gas Management

### Estimating Gas

```python
# Estimate gas for transaction
gas_estimate = blockchain.w3.eth.estimate_gas(transaction)
```

### Setting Gas Price

```python
# Get current gas price
gas_price = blockchain.w3.eth.gas_price

# Or use EIP-1559
transaction['maxFeePerGas'] = blockchain.w3.eth.gas_price * 2
transaction['maxPriorityFeePerGas'] = blockchain.w3.to_wei(2, 'gwei')
```

### Transaction Options

```python
transaction = contract.functions.transfer(to, amount).build_transaction({
    'from': account.address,
    'nonce': nonce,
    'gas': 100000,              # Gas limit
    'gasPrice': gas_price,      # Legacy gas price
    # Or for EIP-1559:
    'maxFeePerGas': max_fee,
    'maxPriorityFeePerGas': priority_fee
})
```

## Testing Contracts

### Local Development

Use Ganache for local testing:

```bash
# Install and run Ganache
npm install -g ganache
ganache --port 8545

# Configure node
BLOCKCHAIN_URL=http://localhost:8545
PRIVATE_KEY=0x... # Ganache provides test accounts
```

### Test Networks

| Network | Faucet |
|---------|--------|
| Sepolia | https://sepoliafaucet.com |
| Mumbai (Polygon) | https://faucet.polygon.technology |
| Goerli | https://goerlifaucet.com |

## Security Considerations

### Private Key Safety

!!! danger "Never Commit Private Keys"
    - Use environment variables
    - Never hardcode in source
    - Use hardware wallets for production

### Contract Security

- **Audit contracts** before mainnet deployment
- **Test thoroughly** on testnets first
- **Use upgradeable patterns** for flexibility
- **Implement access control** for sensitive functions

### Gas Limits

- Set reasonable gas limits to prevent stuck transactions
- Monitor gas prices during high network activity
- Consider gas price oracles for dynamic pricing

## Troubleshooting

### Common Errors

| Error | Cause | Solution |
|-------|-------|----------|
| `Contract artifacts not found` | Missing JSON file | Check contracts directory |
| `Insufficient funds` | Low ETH balance | Fund account with native token |
| `Nonce too low` | Transaction conflict | Wait or manually set nonce |
| `Gas estimation failed` | Invalid transaction | Check function parameters |
| `Connection refused` | RPC not available | Verify blockchain URL |

### Debugging Transactions

```python
# Get transaction receipt
receipt = blockchain.w3.eth.get_transaction_receipt(tx_hash)

print(f"Status: {receipt.status}")  # 1 = success, 0 = failed
print(f"Gas used: {receipt.gasUsed}")
print(f"Block: {receipt.blockNumber}")
```

## See Also

- [Configuration](../getting-started/configuration.md) - Blockchain settings
- [API Reference](../user-guide/api-reference.md) - Token endpoints
- [Security](../operations/security.md) - Key management
