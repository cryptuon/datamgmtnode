import pytest
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.authorisation import AuthorizationModule
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa, padding


def generate_key_pair():
    """Generate an RSA key pair for testing."""
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048
    )
    public_key = private_key.public_key()

    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    ).decode()

    return private_key, public_pem


def sign_data(private_key, data):
    """Sign data with private key."""
    signature = private_key.sign(
        data.encode(),
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH
        ),
        hashes.SHA256()
    )
    return signature


class TestAuthorizationModule:
    @pytest.fixture
    def auth_module(self, temp_sqlite_db):
        """Create an AuthorizationModule instance."""
        return AuthorizationModule(temp_sqlite_db)

    def test_init(self, auth_module):
        """Test AuthorizationModule initialization."""
        assert auth_module.db is not None
        assert auth_module.authorized_keys is not None

    def test_add_authorized_user(self, auth_module):
        """Test adding an authorized user."""
        _, public_pem = generate_key_pair()
        user_id = 'test_user'

        auth_module.add_authorized_user(user_id, public_pem)

        assert user_id in auth_module.authorized_keys
        assert auth_module.authorized_keys[user_id] == public_pem

    def test_authorize_transfer_valid(self, auth_module):
        """Test authorization with valid signature."""
        private_key, public_pem = generate_key_pair()
        user_id = 'valid_user'
        data_hash = 'abc123hash'

        auth_module.add_authorized_user(user_id, public_pem)
        signature = sign_data(private_key, data_hash)

        result = auth_module.authorize_transfer(data_hash, signature, user_id)

        assert result is True

    def test_authorize_transfer_invalid_signature(self, auth_module):
        """Test authorization with invalid signature."""
        _, public_pem = generate_key_pair()
        different_private_key, _ = generate_key_pair()
        user_id = 'user1'
        data_hash = 'abc123hash'

        auth_module.add_authorized_user(user_id, public_pem)
        # Sign with different key
        wrong_signature = sign_data(different_private_key, data_hash)

        result = auth_module.authorize_transfer(data_hash, wrong_signature, user_id)

        assert result is False

    def test_authorize_transfer_unknown_user(self, auth_module):
        """Test authorization for unknown user."""
        result = auth_module.authorize_transfer('hash', b'signature', 'unknown_user')

        assert result is False

    def test_authorize_transfer_wrong_data(self, auth_module):
        """Test authorization with signature for different data."""
        private_key, public_pem = generate_key_pair()
        user_id = 'user1'

        auth_module.add_authorized_user(user_id, public_pem)
        signature = sign_data(private_key, 'original_data')

        result = auth_module.authorize_transfer('different_data', signature, user_id)

        assert result is False

    def test_load_authorized_keys_from_db(self, temp_sqlite_db):
        """Test loading authorized keys from database."""
        # Pre-populate database
        _, public_pem = generate_key_pair()
        temp_sqlite_db.execute(
            "INSERT INTO authorized_users (user_id, public_key) VALUES (?, ?)",
            ('preloaded_user', public_pem)
        )
        temp_sqlite_db.commit()

        # Create new instance to test loading
        auth_module = AuthorizationModule(temp_sqlite_db)

        assert 'preloaded_user' in auth_module.authorized_keys

    def test_add_multiple_users(self, auth_module):
        """Test adding multiple authorized users."""
        for i in range(3):
            _, public_pem = generate_key_pair()
            auth_module.add_authorized_user(f'user_{i}', public_pem)

        assert len(auth_module.authorized_keys) == 3
        assert 'user_0' in auth_module.authorized_keys
        assert 'user_1' in auth_module.authorized_keys
        assert 'user_2' in auth_module.authorized_keys
