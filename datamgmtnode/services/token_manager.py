

# TokenManager
class TokenManager:
    def __init__(self, blockchain_interface, native_token_address):
        self.blockchain = blockchain_interface
        self.supported_tokens = {}
        self.node_tokens = {}
        self.native_token_address = native_token_address

    def update_blockchain_interface(self, new_blockchain_interface):
        self.blockchain = new_blockchain_interface

    def add_supported_token(self, token_address, token_abi):
        self.supported_tokens[token_address] = self.blockchain.w3.eth.contract(address=token_address, abi=token_abi)

    def is_supported_token(self, token_address):
        return token_address in self.supported_tokens or token_address == self.native_token_address

    def get_balance(self, address, token_address):
        if token_address == self.native_token_address:
            return self.blockchain.get_balance(address)
        elif self.is_supported_token(token_address):
            token_contract = self.supported_tokens[token_address]
            return token_contract.functions.balanceOf(address).call()
        else:
            raise ValueError("Unsupported token")

    def issue_new_token(self, name, symbol, initial_supply):
        token_contract = self.blockchain.deploy_contract('ERC20Token', [name, symbol, initial_supply])
        token_address = token_contract.address
        self.node_tokens[symbol] = token_address
        self.add_supported_token(token_address, token_contract.abi)
        return token_address

    def mint_tokens(self, token_address, recipient, amount):
        if token_address not in self.node_tokens.values():
            raise ValueError("Can only mint tokens issued by this node")
        tx_hash = self.blockchain.call_contract_function(token_address, 'mint', [recipient, amount])
        return tx_hash

    def transfer_tokens(self, token_address, from_address, to_address, amount):
        if token_address == self.native_token_address:
            tx_hash = self.blockchain.send_transaction({
                'from': from_address,
                'to': to_address,
                'value': amount
            })
        elif self.is_supported_token(token_address):
            tx_hash = self.blockchain.call_contract_function(token_address, 'transfer', [to_address, amount])
        else:
            raise ValueError("Unsupported token")
        return tx_hash
