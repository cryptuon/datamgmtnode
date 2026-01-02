import asyncio
import time
import hashlib
import sqlite3
import logging
import re
import os
from blockchain.evm_blockchain_interface import EVMBlockchainInterface
from services.data_manager import DataManager
from services.token_manager import TokenManager
from services.payment_processor import PaymentProcessor
from services.compliance_manager import ComplianceManager
from services.authorisation import AuthorizationModule
from services.plugin_manager import PluginManager
from services.key_manager import KeyManager
from network.p2p_network import P2PNetwork
from api.internal_api import InternalAPI
from api.external_api import ExternalAPI

logger = logging.getLogger(__name__)

class ConfigurationError(Exception):
    """Raised when configuration validation fails."""
    pass


# Configuration class
class NodeConfig:
    SUPPORTED_BLOCKCHAIN_TYPES = ['evm']
    ETH_ADDRESS_PATTERN = re.compile(r'^0x[a-fA-F0-9]{40}$')

    def __init__(self, blockchain_type, blockchain_url, private_key, native_token_address,
                 db_path, sqlite_db_path, p2p_port, plugin_dir, node_id, node_signature,
                 initial_peers, data_dir=None):
        self.blockchain_type = blockchain_type
        self.blockchain_url = blockchain_url
        self.private_key = private_key
        self.native_token_address = native_token_address
        self.db_path = db_path
        self.sqlite_db_path = sqlite_db_path
        self.p2p_port = p2p_port
        self.plugin_dir = plugin_dir
        self.node_id = node_id
        self.node_signature = node_signature
        self.initial_peers = initial_peers
        self.data_dir = data_dir or './data'

    def validate(self):
        """Validate configuration and raise ConfigurationError if invalid."""
        errors = []

        # Validate blockchain type
        if self.blockchain_type not in self.SUPPORTED_BLOCKCHAIN_TYPES:
            errors.append(f"Unsupported blockchain_type: {self.blockchain_type}. "
                          f"Supported: {self.SUPPORTED_BLOCKCHAIN_TYPES}")

        # Validate blockchain URL
        if not self.blockchain_url:
            errors.append("blockchain_url is required")
        elif not self.blockchain_url.startswith(('http://', 'https://', 'ws://', 'wss://')):
            errors.append("blockchain_url must start with http://, https://, ws://, or wss://")

        # Validate native token address
        if self.native_token_address and not self.ETH_ADDRESS_PATTERN.match(self.native_token_address):
            errors.append(f"Invalid native_token_address format: {self.native_token_address}")

        # Validate port
        if not isinstance(self.p2p_port, int) or not (1 <= self.p2p_port <= 65535):
            errors.append(f"p2p_port must be an integer between 1 and 65535, got: {self.p2p_port}")

        # Validate node_id
        if not self.node_id or not isinstance(self.node_id, str):
            errors.append("node_id is required and must be a string")
        elif len(self.node_id) > 100:
            errors.append("node_id must be 100 characters or less")

        # Validate paths - create directories if they don't exist
        for path_name, path_val in [('db_path', self.db_path), ('data_dir', self.data_dir)]:
            if path_val:
                try:
                    os.makedirs(path_val, exist_ok=True)
                except OSError as e:
                    errors.append(f"Cannot create {path_name} directory '{path_val}': {e}")

        # Validate sqlite_db_path directory
        if self.sqlite_db_path:
            sqlite_dir = os.path.dirname(self.sqlite_db_path)
            if sqlite_dir:
                try:
                    os.makedirs(sqlite_dir, exist_ok=True)
                except OSError as e:
                    errors.append(f"Cannot create sqlite_db_path directory '{sqlite_dir}': {e}")

        # Validate initial_peers format
        if self.initial_peers:
            for peer in self.initial_peers:
                if not peer.startswith(('http://', 'https://')):
                    errors.append(f"Invalid peer URL: {peer}. Must start with http:// or https://")

        if errors:
            raise ConfigurationError("Configuration validation failed:\n  - " + "\n  - ".join(errors))

        return True

class Node:
    def __init__(self, config):
        self.config = config
        self.blockchain_interface = self._init_blockchain_interface()
        self.db_connection = self._init_database()
        self.data_manager = DataManager(config.db_path)
        self.token_manager = TokenManager(self.blockchain_interface, config.native_token_address)
        self.payment_processor = PaymentProcessor(self.blockchain_interface, self.token_manager)
        self.compliance_manager = ComplianceManager(self.blockchain_interface)
        self.authorization_module = AuthorizationModule(self.db_connection)
        self.p2p_network = P2PNetwork(self, config.p2p_port, config.initial_peers, config.data_dir)
        self.plugin_manager = PluginManager(self, config.plugin_dir)
        self.internal_api = InternalAPI(self)
        self.external_api = ExternalAPI(self)

        # Initialize secure key management
        self.key_manager = KeyManager(config.data_dir)
        self.cipher_suite = self.key_manager.initialize()
        logger.info(f"Encryption key initialized (version {self.key_manager.current_version})")

    def _init_blockchain_interface(self):
        if self.config.blockchain_type == 'evm':
            return EVMBlockchainInterface(self.config.blockchain_url, self.config.private_key)
        else:
            raise ValueError(f"Unsupported blockchain type: {self.config.blockchain_type}")

    def _init_database(self):
        conn = sqlite3.connect(self.config.sqlite_db_path)
        conn.execute('''CREATE TABLE IF NOT EXISTS authorized_users
                        (user_id TEXT PRIMARY KEY, public_key TEXT)''')
        conn.commit()
        return conn

    async def start(self):
        if not self.blockchain_interface.connect():
            raise ConnectionError("Failed to connect to the blockchain")
        
        self.plugin_manager.load_plugins()
        
        await asyncio.gather(
            self.p2p_network.start(),
            self.internal_api.start(),
            self.external_api.start()
        )

    async def stop(self):
        """Stop all node components with proper error handling."""
        errors = []

        # Stop APIs first (they depend on other services)
        try:
            await self.internal_api.stop()
        except Exception as e:
            logger.error(f"Error stopping internal API: {e}")
            errors.append(e)

        try:
            await self.external_api.stop()
        except Exception as e:
            logger.error(f"Error stopping external API: {e}")
            errors.append(e)

        # Stop P2P network
        try:
            await self.p2p_network.stop()
        except Exception as e:
            logger.error(f"Error stopping P2P network: {e}")
            errors.append(e)

        # Shutdown plugins
        try:
            self.plugin_manager.shutdown_plugins()
        except Exception as e:
            logger.error(f"Error shutting down plugins: {e}")
            errors.append(e)

        # Disconnect blockchain
        try:
            self.blockchain_interface.disconnect()
        except Exception as e:
            logger.error(f"Error disconnecting blockchain: {e}")
            errors.append(e)

        # Close databases
        try:
            self.db_connection.close()
        except Exception as e:
            logger.error(f"Error closing SQLite connection: {e}")
            errors.append(e)

        try:
            self.data_manager.close()
        except Exception as e:
            logger.error(f"Error closing data manager: {e}")
            errors.append(e)

        if errors:
            logger.warning(f"Node stopped with {len(errors)} error(s)")

    def change_blockchain(self, new_blockchain_type, new_blockchain_url, new_private_key):
        self.blockchain_interface.disconnect()
        self.config.blockchain_type = new_blockchain_type
        self.config.blockchain_url = new_blockchain_url
        self.config.private_key = new_private_key
        self.blockchain_interface = self._init_blockchain_interface()
        if not self.blockchain_interface.connect():
            raise ConnectionError("Failed to connect to the new blockchain")
        self.token_manager.update_blockchain_interface(self.blockchain_interface)
        self.payment_processor.update_blockchain_interface(self.blockchain_interface)
        self.compliance_manager.update_blockchain_interface(self.blockchain_interface)

    def get_native_token_address(self):
        return self.config.native_token_address
    
    async def share_data(self, data, recipient, payment_token=None, payment_amount=None):
        data_hash = self._hash_data(data)

        if not self.authorization_module.authorize_transfer(data_hash, self.config.node_signature, self.config.node_id):
            raise ValueError("Unauthorized data transfer")

        if payment_token and payment_amount:
            success, tx_hash = self.payment_processor.process_payment(
                recipient, self.blockchain_interface.account.address,
                payment_amount, payment_token
            )
            if not success:
                raise ValueError("Payment failed")

        self.data_manager.store_data(data_hash, data)
        await self.p2p_network.send_data(data_hash, data)

        event_data = {
            'data_hash': data_hash,
            'recipient': recipient,
            'payment_tx_hash': tx_hash if payment_token else None,
            'timestamp': int(time.time())
        }
        compliance_tx_hash = self.compliance_manager.record_compliance_event('data_share', event_data)

        return compliance_tx_hash

    def _hash_data(self, data):
        return hashlib.sha256(str(data).encode()).hexdigest()

    def encrypt_data(self, data):
        return self.cipher_suite.encrypt(str(data).encode()).decode()

    def decrypt_data(self, encrypted_data):
        return self.cipher_suite.decrypt(encrypted_data.encode()).decode()

    async def on_data_received(self, data_hash, data):
        # This method can be overridden or extended to handle incoming data
        logger.info(f"Received data with hash: {data_hash}")
        # You might want to trigger some events, update UI, or process the data further

    async def get_shared_data(self, data_hash):
        # First, try to get the data from local storage
        data = self.data_manager.get_data(data_hash)
        if data is None:
            # If not found locally, try to fetch from the P2P network
            data = await self.p2p_network.get_data(data_hash)
            if data:
                # If found on the network, store it locally for future use
                self.data_manager.store_data(data_hash, data)
        return data