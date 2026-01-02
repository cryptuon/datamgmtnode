from abc import ABC, abstractmethod


class BlockchainInterface(ABC):
    @abstractmethod
    def connect(self):
        pass

    @abstractmethod
    def disconnect(self):
        pass

    @abstractmethod
    def get_balance(self, address):
        pass

    @abstractmethod
    def send_transaction(self, transaction):
        pass

    @abstractmethod
    def deploy_contract(self, contract_name, args):
        pass

    @abstractmethod
    def call_contract_function(self, contract_address, function_name, args):
        pass