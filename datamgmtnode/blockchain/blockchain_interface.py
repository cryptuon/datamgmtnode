import os
import time
import hashlib
from abc import ABC, abstractmethod
from web3 import Web3
from eth_account import Account
import rocksdb
import sqlite3
import asyncio
import aiohttp
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.asymmetric import padding, rsa

# BlockchainInterface
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