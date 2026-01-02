import json
import os
from blockchain.blockchain_interface import BlockchainInterface
from web3 import Web3
from eth_account import Account


class EVMBlockchainInterface(BlockchainInterface):
    def __init__(self, network_url, private_key, contracts_dir=None):
        self.network_url = network_url
        self.private_key = private_key
        self.contracts_dir = contracts_dir or './contracts'
        self.w3 = None
        self.account = None
        self._contract_abis = {}  # Cache for contract ABIs

    def connect(self):
        self.w3 = Web3(Web3.HTTPProvider(self.network_url))
        self.account = Account.from_key(self.private_key)
        return self.w3.is_connected()

    def disconnect(self):
        self.w3 = None
        self.account = None

    def get_balance(self, address):
        return self.w3.eth.get_balance(address)

    def send_transaction(self, transaction):
        """Send a transaction and return the transaction hash."""
        # Ensure transaction has required fields
        if 'nonce' not in transaction:
            transaction['nonce'] = self.w3.eth.get_transaction_count(self.account.address)
        if 'gas' not in transaction:
            transaction['gas'] = self.w3.eth.estimate_gas(transaction)
        if 'gasPrice' not in transaction and 'maxFeePerGas' not in transaction:
            transaction['gasPrice'] = self.w3.eth.gas_price

        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.raw_transaction)
        return tx_hash.hex()

    def wait_for_receipt(self, tx_hash):
        """Wait for a transaction receipt."""
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def deploy_contract(self, contract_name, args):
        abi, bytecode = self.get_contract_artifacts(contract_name)
        if abi is None or bytecode is None:
            raise ValueError(f"Contract artifacts not found for: {contract_name}")

        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        transaction = contract.constructor(*args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        tx_hash = self.send_transaction(transaction)
        tx_receipt = self.wait_for_receipt(tx_hash)

        # Cache the ABI for the deployed contract
        self._contract_abis[tx_receipt.contractAddress] = abi

        return self.w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

    def call_contract_function(self, contract_address, function_name, args):
        abi = self.get_contract_abi(contract_address)
        if abi is None:
            raise ValueError(f"ABI not found for contract: {contract_address}")

        contract = self.w3.eth.contract(address=contract_address, abi=abi)
        return getattr(contract.functions, function_name)(*args).call()

    def get_contract_artifacts(self, contract_name):
        """Load contract ABI and bytecode from JSON file."""
        artifact_path = os.path.join(self.contracts_dir, f'{contract_name}.json')

        if not os.path.exists(artifact_path):
            return None, None

        with open(artifact_path, 'r') as f:
            artifact = json.load(f)

        abi = artifact.get('abi')
        bytecode = artifact.get('bytecode') or artifact.get('bin')

        return abi, bytecode

    def get_contract_abi(self, contract_address):
        """Get ABI for a contract address from cache or storage."""
        # Check cache first
        if contract_address in self._contract_abis:
            return self._contract_abis[contract_address]

        # Try to load from a stored mapping file
        mapping_path = os.path.join(self.contracts_dir, 'deployed_contracts.json')
        if os.path.exists(mapping_path):
            with open(mapping_path, 'r') as f:
                mappings = json.load(f)
                if contract_address in mappings:
                    contract_name = mappings[contract_address]
                    abi, _ = self.get_contract_artifacts(contract_name)
                    if abi:
                        self._contract_abis[contract_address] = abi
                        return abi

        return None