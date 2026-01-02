import pytest
import tempfile
import os
import sqlite3
from unittest.mock import Mock, MagicMock


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for database tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield os.path.join(tmpdir, 'test_db')


@pytest.fixture
def temp_sqlite_db():
    """Create a temporary SQLite database."""
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name

    conn = sqlite3.connect(db_path)
    conn.execute('''CREATE TABLE IF NOT EXISTS authorized_users
                    (user_id TEXT PRIMARY KEY, public_key TEXT)''')
    conn.commit()

    yield conn

    conn.close()
    os.unlink(db_path)


@pytest.fixture
def mock_blockchain():
    """Create a mock blockchain interface."""
    mock = Mock()
    mock.w3 = Mock()
    mock.account = Mock()
    mock.account.address = '0x1234567890abcdef1234567890abcdef12345678'

    # Mock common methods
    mock.connect.return_value = True
    mock.get_balance.return_value = 1000000000000000000  # 1 ETH in wei
    mock.send_transaction.return_value = '0xabcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890'
    mock.wait_for_receipt.return_value = {'status': 1, 'transactionHash': b'\xab\xcd\xef'}

    # Mock Web3 methods
    mock.w3.eth = Mock()
    mock.w3.eth.get_balance.return_value = 1000000000000000000
    mock.w3.eth.get_transaction_count.return_value = 0
    mock.w3.eth.gas_price = 20000000000
    mock.w3.eth.estimate_gas.return_value = 21000
    mock.w3.eth.contract.return_value = Mock()
    mock.w3.to_checksum_address.side_effect = lambda x: x
    mock.w3.to_hex.side_effect = lambda text='': f'0x{text.encode().hex()}' if text else '0x'

    return mock


@pytest.fixture
def mock_token_manager(mock_blockchain):
    """Create a mock token manager."""
    mock = Mock()
    mock.is_supported_token.return_value = True
    mock.get_balance.return_value = 1000000000000000000
    mock.transfer_tokens.return_value = '0xabcdef1234567890'
    return mock
