class TokenManager:
    def __init__(self, blockchain_interface, native_token_address):
        self.blockchain = blockchain_interface
        self.supported_tokens = {}
        self.node_tokens = {}
        self.native_token_address = native_token_address

    def update_blockchain_interface(self, new_blockchain_interface):
        self.blockchain = new_blockchain_interface

    def add_supported_token(self, token_address, token_abi):
        self.supported_tokens[token_address] = {
            'address': token_address,
            'abi': token_abi,
            'contract': self.blockchain.w3.eth.contract(address=token_address, abi=token_abi)
        }

    def is_supported_token(self, token_address):
        return token_address in self.supported_tokens or token_address == self.native_token_address

    def get_balance(self, address, token_address):
        if token_address == self.native_token_address:
            return self.blockchain.get_balance(address)
        elif token_address in self.supported_tokens:
            token_contract = self.supported_tokens[token_address]['contract']
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
        return self._send_token_transaction(token_address, 'mint', [recipient, amount])

    def transfer_tokens(self, token_address, from_address, to_address, amount):
        if token_address == self.native_token_address:
            tx_hash = self.blockchain.send_transaction({
                'from': from_address,
                'to': to_address,
                'value': amount
            })
        elif token_address in self.supported_tokens:
            tx_hash = self._send_token_transaction(token_address, 'transfer', [to_address, amount])
        else:
            raise ValueError("Unsupported token")
        return tx_hash

    def _send_token_transaction(self, token_address, function_name, args):
        """Build and send a transaction to a token contract."""
        if token_address not in self.supported_tokens:
            raise ValueError(f"Token not supported: {token_address}")

        token_contract = self.supported_tokens[token_address]['contract']
        func = getattr(token_contract.functions, function_name)(*args)

        transaction = func.build_transaction({
            'from': self.blockchain.account.address,
            'nonce': self.blockchain.w3.eth.get_transaction_count(self.blockchain.account.address),
        })

        return self.blockchain.send_transaction(transaction)
