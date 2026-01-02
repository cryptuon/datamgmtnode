import pytest
import sys
import os
import json
import tempfile
from unittest.mock import patch

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.key_manager import KeyManager


class TestKeyManager:
    """Tests for KeyManager secure key storage."""

    def test_init_creates_keys_file(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()

            keys_file = os.path.join(tmpdir, 'encryption_keys.json')
            assert os.path.exists(keys_file)

    def test_init_generates_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            cipher = manager.initialize()

            assert cipher is not None
            assert manager.current_version == 1

    def test_key_persistence_across_restarts(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # First initialization
            manager1 = KeyManager(tmpdir, master_password='test_password')
            cipher1 = manager1.initialize()

            # Encrypt some data
            test_data = b"sensitive information"
            encrypted = cipher1.encrypt(test_data)

            # Simulate restart with new manager instance
            manager2 = KeyManager(tmpdir, master_password='test_password')
            cipher2 = manager2.initialize()

            # Should be able to decrypt with the reloaded key
            decrypted = cipher2.decrypt(encrypted)
            assert decrypted == test_data

    def test_key_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()
            assert manager.current_version == 1

            # Rotate key
            manager.rotate_key()
            assert manager.current_version == 2

            # Check keys file has both versions
            keys_file = os.path.join(tmpdir, 'encryption_keys.json')
            with open(keys_file, 'r') as f:
                data = json.load(f)
            assert len(data['keys']) == 2

    def test_decrypt_with_old_key_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            cipher_v1 = manager.initialize()

            # Encrypt with version 1
            test_data = b"sensitive data v1"
            encrypted_v1 = cipher_v1.encrypt(test_data)

            # Rotate to version 2
            manager.rotate_key()

            # Old encrypted data should still be decryptable
            old_cipher = manager.get_cipher(version=1)
            decrypted = old_cipher.decrypt(encrypted_v1)
            assert decrypted == test_data

    def test_current_cipher_uses_latest_key(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()
            manager.rotate_key()
            manager.rotate_key()

            assert manager.current_version == 3
            current_cipher = manager.get_current_cipher()
            assert current_cipher is not None

    def test_wrong_password_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            # Create keys with one password
            manager1 = KeyManager(tmpdir, master_password='correct_password')
            manager1.initialize()

            # Try to load with wrong password
            manager2 = KeyManager(tmpdir, master_password='wrong_password')
            with pytest.raises(Exception):
                manager2.initialize()

    def test_keys_encrypted_at_rest(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()

            # Read raw file contents
            keys_file = os.path.join(tmpdir, 'encryption_keys.json')
            with open(keys_file, 'r') as f:
                data = json.load(f)

            # Keys should be encrypted (not plain base64 Fernet keys)
            assert 'salt' in data
            assert 'keys' in data
            for version, encrypted_key in data['keys'].items():
                # Encrypted keys should be longer than plain Fernet keys
                # Plain Fernet keys are 44 chars base64, encrypted will be longer
                assert len(encrypted_key) > 50

    def test_empty_password_uses_env_var(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            with patch.dict(os.environ, {'KEY_MASTER_PASSWORD': 'env_password'}):
                manager = KeyManager(tmpdir)  # No explicit password
                cipher = manager.initialize()
                assert cipher is not None

    def test_key_versions_after_rotation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()
            manager.rotate_key()
            manager.rotate_key()

            # Check all versions have cipher suites
            assert 1 in manager._cipher_suites
            assert 2 in manager._cipher_suites
            assert 3 in manager._cipher_suites
            assert manager.current_version == 3

    def test_get_nonexistent_version_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test_password')
            manager.initialize()

            with pytest.raises(ValueError):
                manager.get_cipher(version=999)

    def test_keys_directory_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            keys_dir = os.path.join(tmpdir, 'subdir', 'keys')
            manager = KeyManager(keys_dir, master_password='test_password')
            manager.initialize()

            assert os.path.exists(keys_dir)
            assert os.path.isfile(os.path.join(keys_dir, 'encryption_keys.json'))


class TestKeyManagerEncryption:
    """Tests for KeyManager encryption functionality."""

    def test_encrypt_decrypt_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test')
            cipher = manager.initialize()

            original = b"Hello, World!"
            encrypted = cipher.encrypt(original)
            decrypted = cipher.decrypt(encrypted)

            assert decrypted == original
            assert encrypted != original

    def test_encrypt_produces_different_output(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            manager = KeyManager(tmpdir, master_password='test')
            cipher = manager.initialize()

            data = b"same data"
            encrypted1 = cipher.encrypt(data)
            encrypted2 = cipher.encrypt(data)

            # Fernet uses random IV, so same input produces different output
            assert encrypted1 != encrypted2

    def test_decrypt_wrong_key_fails(self):
        with tempfile.TemporaryDirectory() as tmpdir1, \
                tempfile.TemporaryDirectory() as tmpdir2:

            manager1 = KeyManager(tmpdir1, master_password='test')
            cipher1 = manager1.initialize()

            manager2 = KeyManager(tmpdir2, master_password='test')
            cipher2 = manager2.initialize()

            encrypted = cipher1.encrypt(b"secret")

            with pytest.raises(Exception):
                cipher2.decrypt(encrypted)
