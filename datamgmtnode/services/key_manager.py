import os
import json
import base64
import logging
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

logger = logging.getLogger(__name__)


class KeyManager:
    """
    Secure encryption key management with persistence.

    Keys are encrypted at rest using a master password and PBKDF2 key derivation.
    Supports key versioning for rotation.
    """

    def __init__(self, keys_dir: str, master_password: str = None):
        self.keys_dir = keys_dir
        self.keys_file = os.path.join(keys_dir, 'encryption_keys.json')
        self._master_password = master_password or os.getenv('KEY_MASTER_PASSWORD', '')
        self._keys: dict[int, bytes] = {}
        self._current_version: int = 0
        self._cipher_suites: dict[int, Fernet] = {}

        if not self._master_password:
            logger.warning("No master password set - keys will be stored with default protection")
            self._master_password = 'default-insecure-password'

    def initialize(self) -> Fernet:
        """Initialize the key manager and return the current cipher suite."""
        os.makedirs(self.keys_dir, exist_ok=True)

        if os.path.exists(self.keys_file):
            self._load_keys()
        else:
            self._generate_new_key()
            self._save_keys()

        return self.get_current_cipher()

    def _derive_master_key(self, salt: bytes) -> bytes:
        """Derive encryption key from master password using PBKDF2."""
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        return base64.urlsafe_b64encode(kdf.derive(self._master_password.encode()))

    def _generate_new_key(self) -> int:
        """Generate a new encryption key and return its version."""
        new_version = self._current_version + 1
        new_key = Fernet.generate_key()

        self._keys[new_version] = new_key
        self._cipher_suites[new_version] = Fernet(new_key)
        self._current_version = new_version

        logger.info(f"Generated new encryption key version {new_version}")
        return new_version

    def _save_keys(self):
        """Save all keys encrypted to disk."""
        salt = os.urandom(16)
        master_key = self._derive_master_key(salt)
        master_cipher = Fernet(master_key)

        encrypted_keys = {}
        for version, key in self._keys.items():
            encrypted_key = master_cipher.encrypt(key)
            encrypted_keys[str(version)] = base64.b64encode(encrypted_key).decode()

        data = {
            'salt': base64.b64encode(salt).decode(),
            'current_version': self._current_version,
            'keys': encrypted_keys
        }

        with open(self.keys_file, 'w') as f:
            json.dump(data, f, indent=2)

        # Set restrictive permissions
        os.chmod(self.keys_file, 0o600)
        logger.info(f"Saved {len(self._keys)} encryption key(s) to disk")

    def _load_keys(self):
        """Load and decrypt keys from disk."""
        try:
            with open(self.keys_file, 'r') as f:
                data = json.load(f)

            salt = base64.b64decode(data['salt'])
            master_key = self._derive_master_key(salt)
            master_cipher = Fernet(master_key)

            self._current_version = data['current_version']

            for version_str, encrypted_key_b64 in data['keys'].items():
                version = int(version_str)
                encrypted_key = base64.b64decode(encrypted_key_b64)
                key = master_cipher.decrypt(encrypted_key)

                self._keys[version] = key
                self._cipher_suites[version] = Fernet(key)

            logger.info(f"Loaded {len(self._keys)} encryption key(s), current version: {self._current_version}")

        except Exception as e:
            logger.error(f"Failed to load encryption keys: {e}")
            raise RuntimeError(f"Cannot load encryption keys: {e}")

    def get_current_cipher(self) -> Fernet:
        """Get the cipher suite for the current key version."""
        if self._current_version not in self._cipher_suites:
            raise RuntimeError("No encryption key available")
        return self._cipher_suites[self._current_version]

    def get_cipher(self, version: int) -> Fernet:
        """Get cipher suite for a specific key version (for decrypting old data)."""
        if version not in self._cipher_suites:
            raise ValueError(f"Unknown key version: {version}")
        return self._cipher_suites[version]

    def rotate_key(self) -> int:
        """Generate a new key version for rotation."""
        new_version = self._generate_new_key()
        self._save_keys()
        return new_version

    @property
    def current_version(self) -> int:
        """Get the current key version."""
        return self._current_version

    def encrypt(self, data: str) -> dict:
        """Encrypt data and return with version metadata."""
        cipher = self.get_current_cipher()
        encrypted = cipher.encrypt(data.encode())
        return {
            'version': self._current_version,
            'data': encrypted.decode()
        }

    def decrypt(self, encrypted_data: dict) -> str:
        """Decrypt data using the appropriate key version."""
        version = encrypted_data.get('version', 1)
        data = encrypted_data.get('data', encrypted_data)

        # Handle legacy format (just encrypted string)
        if isinstance(data, str):
            cipher = self.get_cipher(version)
            return cipher.decrypt(data.encode()).decode()

        raise ValueError("Invalid encrypted data format")

    def decrypt_legacy(self, encrypted_string: str) -> str:
        """Decrypt data encrypted with the current key (legacy format)."""
        cipher = self.get_current_cipher()
        return cipher.decrypt(encrypted_string.encode()).decode()
