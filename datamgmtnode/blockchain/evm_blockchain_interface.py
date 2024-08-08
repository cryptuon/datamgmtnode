from blockchain.blockchain_interface import BlockchainInterface
import Web3

class EVMBlockchainInterface(BlockchainInterface):
    def __init__(self, network_url, private_key):
        self.network_url = network_url
        self.private_key = private_key
        self.w3 = None
        self.account = None

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
        signed_txn = self.w3.eth.account.sign_transaction(transaction, self.private_key)
        tx_hash = self.w3.eth.send_raw_transaction(signed_txn.rawTransaction)
        return self.w3.eth.wait_for_transaction_receipt(tx_hash)

    def deploy_contract(self, contract_name, args):
        abi, bytecode = self.get_contract_artifacts(contract_name)
        contract = self.w3.eth.contract(abi=abi, bytecode=bytecode)
        transaction = contract.constructor(*args).build_transaction({
            'from': self.account.address,
            'nonce': self.w3.eth.get_transaction_count(self.account.address),
        })
        tx_receipt = self.send_transaction(transaction)
        return self.w3.eth.contract(address=tx_receipt.contractAddress, abi=abi)

    def call_contract_function(self, contract_address, function_name, args):
        abi = self.get_contract_abi(contract_address)
        contract = self.w3.eth.contract(address=contract_address, abi=abi)
        return getattr(contract.functions, function_name)(*args).call()

    def get_contract_artifacts(self, contract_name):
        # Implementation depends on how you store/manage your contract artifacts
        pass

    def get_contract_abi(self, contract_address):
        # Implementation depends on how you store/manage your contract ABIs
        pass