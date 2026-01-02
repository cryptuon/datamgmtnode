import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.token_manager import TokenManager


class TestTokenManager:
    @pytest.fixture
    def token_manager(self, mock_blockchain):
        """Create a TokenManager instance with mock blockchain."""
        native_token = '0xNativeToken1234567890123456789012345678'
        return TokenManager(mock_blockchain, native_token)

    def test_init(self, token_manager):
        """Test TokenManager initialization."""
        assert token_manager.blockchain is not None
        assert token_manager.native_token_address is not None
        assert token_manager.supported_tokens == {}
        assert token_manager.node_tokens == {}

    def test_is_supported_token_native(self, token_manager):
        """Test that native token is always supported."""
        assert token_manager.is_supported_token(token_manager.native_token_address) is True

    def test_is_supported_token_unsupported(self, token_manager):
        """Test that unknown tokens are not supported."""
        assert token_manager.is_supported_token('0xUnknownToken') is False

    def test_add_supported_token(self, token_manager):
        """Test adding a supported token."""
        token_address = '0xNewToken12345678901234567890123456789012'
        mock_abi = [{'name': 'transfer', 'type': 'function'}]

        token_manager.add_supported_token(token_address, mock_abi)

        assert token_manager.is_supported_token(token_address) is True
        assert token_address in token_manager.supported_tokens

    def test_get_balance_native_token(self, token_manager):
        """Test getting balance of native token."""
        address = '0xUser1234567890123456789012345678901234'

        balance = token_manager.get_balance(address, token_manager.native_token_address)

        token_manager.blockchain.get_balance.assert_called_once_with(address)
        assert balance == 1000000000000000000

    def test_get_balance_unsupported_token(self, token_manager):
        """Test getting balance of unsupported token raises error."""
        with pytest.raises(ValueError, match="Unsupported token"):
            token_manager.get_balance('0xUser', '0xUnsupportedToken')

    def test_transfer_tokens_native(self, token_manager):
        """Test transferring native tokens."""
        from_addr = '0xFrom1234567890123456789012345678901234'
        to_addr = '0xTo12345678901234567890123456789012345678'
        amount = 1000

        tx_hash = token_manager.transfer_tokens(
            token_manager.native_token_address,
            from_addr,
            to_addr,
            amount
        )

        assert tx_hash is not None
        token_manager.blockchain.send_transaction.assert_called_once()

    def test_transfer_tokens_unsupported(self, token_manager):
        """Test transferring unsupported token raises error."""
        with pytest.raises(ValueError, match="Unsupported token"):
            token_manager.transfer_tokens('0xUnsupported', '0xFrom', '0xTo', 100)

    def test_update_blockchain_interface(self, token_manager, mock_blockchain):
        """Test updating blockchain interface."""
        new_blockchain = Mock()
        token_manager.update_blockchain_interface(new_blockchain)
        assert token_manager.blockchain == new_blockchain

    def test_mint_tokens_not_node_token(self, token_manager):
        """Test minting tokens not issued by node raises error."""
        with pytest.raises(ValueError, match="Can only mint tokens issued by this node"):
            token_manager.mint_tokens('0xExternalToken', '0xRecipient', 1000)
