import pytest
import sys
import os
from unittest.mock import Mock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.payment_processor import PaymentProcessor


class TestPaymentProcessor:
    @pytest.fixture
    def payment_processor(self, mock_blockchain, mock_token_manager):
        """Create a PaymentProcessor instance with mocks."""
        return PaymentProcessor(mock_blockchain, mock_token_manager)

    def test_init(self, payment_processor, mock_blockchain, mock_token_manager):
        """Test PaymentProcessor initialization."""
        assert payment_processor.blockchain == mock_blockchain
        assert payment_processor.token_manager == mock_token_manager

    def test_process_payment_success(self, payment_processor):
        """Test successful payment processing."""
        from_addr = '0xFrom1234567890123456789012345678901234'
        to_addr = '0xTo12345678901234567890123456789012345678'
        amount = 1000
        token = '0xToken123456789012345678901234567890123'

        success, tx_hash = payment_processor.process_payment(
            from_addr, to_addr, amount, token
        )

        assert success is True
        assert tx_hash is not None

    def test_process_payment_unsupported_token(self, payment_processor):
        """Test payment with unsupported token."""
        payment_processor.token_manager.is_supported_token.return_value = False

        with pytest.raises(ValueError, match="Unsupported token"):
            payment_processor.process_payment(
                '0xFrom', '0xTo', 1000, '0xUnsupportedToken'
            )

    def test_process_payment_insufficient_balance(self, payment_processor):
        """Test payment with insufficient balance."""
        payment_processor.token_manager.get_balance.return_value = 100

        with pytest.raises(ValueError, match="Insufficient balance"):
            payment_processor.process_payment(
                '0xFrom', '0xTo', 1000, '0xToken'
            )

    def test_process_payment_failed_transaction(self, payment_processor):
        """Test handling of failed transaction."""
        payment_processor.blockchain.wait_for_receipt.return_value = {'status': 0}

        success, tx_hash = payment_processor.process_payment(
            '0xFrom', '0xTo', 100, '0xToken'
        )

        assert success is False

    def test_update_blockchain_interface(self, payment_processor):
        """Test updating blockchain interface."""
        new_blockchain = Mock()
        payment_processor.update_blockchain_interface(new_blockchain)
        assert payment_processor.blockchain == new_blockchain

    def test_get_transaction_history(self, payment_processor):
        """Test getting transaction history."""
        address = '0xUser1234567890123456789012345678901234'
        payment_processor.blockchain.w3.eth.get_transaction_count.return_value = 42

        count = payment_processor.get_transaction_history(address)

        assert count == 42
        payment_processor.blockchain.w3.eth.get_transaction_count.assert_called_once_with(address)
