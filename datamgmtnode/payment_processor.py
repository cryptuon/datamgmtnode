
# PaymentProcessor
class PaymentProcessor:
    def __init__(self, blockchain_interface, token_manager):
        self.blockchain = blockchain_interface
        self.token_manager = token_manager

    def update_blockchain_interface(self, new_blockchain_interface):
        self.blockchain = new_blockchain_interface

    def process_payment(self, from_address, to_address, amount, token_address):
        if not self.token_manager.is_supported_token(token_address):
            raise ValueError("Unsupported token")

        balance = self.token_manager.get_balance(from_address, token_address)
        if balance < amount:
            raise ValueError("Insufficient balance")

        tx_hash = self.token_manager.transfer_tokens(token_address, from_address, to_address, amount)
        receipt = self.blockchain.w3.eth.wait_for_transaction_receipt(tx_hash)

        if receipt['status'] == 1:
            return True, tx_hash
        else:
            return False, tx_hash

    def get_transaction_history(self, address):
        # Fetch transaction history from blockchain
        return self.blockchain.w3.eth.get_transaction_count(address)
