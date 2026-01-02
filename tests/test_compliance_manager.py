import pytest
import sys
import os
from unittest.mock import Mock, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.compliance_manager import ComplianceManager


class TestComplianceManager:
    @pytest.fixture
    def compliance_manager(self, mock_blockchain):
        """Create a ComplianceManager instance with mock blockchain."""
        return ComplianceManager(mock_blockchain)

    def test_init(self, compliance_manager, mock_blockchain):
        """Test ComplianceManager initialization."""
        assert compliance_manager.blockchain == mock_blockchain

    def test_record_compliance_event(self, compliance_manager):
        """Test recording a compliance event."""
        event_type = 'data_share'
        event_data = {'data_hash': 'abc123', 'recipient': '0xUser'}

        tx_hash = compliance_manager.record_compliance_event(event_type, event_data)

        assert tx_hash is not None
        compliance_manager.blockchain.send_transaction.assert_called_once()

    def test_record_compliance_event_structure(self, compliance_manager):
        """Test that compliance event transaction is structured correctly."""
        event_type = 'data_share'
        event_data = {'key': 'value'}

        compliance_manager.record_compliance_event(event_type, event_data)

        call_args = compliance_manager.blockchain.send_transaction.call_args
        tx_data = call_args[0][0]

        assert 'from' in tx_data
        assert 'to' in tx_data
        assert 'data' in tx_data

    def test_update_blockchain_interface(self, compliance_manager):
        """Test updating blockchain interface."""
        new_blockchain = Mock()
        compliance_manager.update_blockchain_interface(new_blockchain)
        assert compliance_manager.blockchain == new_blockchain

    def test_verify_compliance_not_found(self, compliance_manager):
        """Test verification when event is not found."""
        # Mock empty blocks
        mock_block = {'number': 100, 'transactions': []}
        compliance_manager.blockchain.w3.eth.get_block.return_value = mock_block

        result = compliance_manager.verify_compliance('data_share', 'nonexistent')

        assert result is False

    def test_get_compliance_history_empty(self, compliance_manager):
        """Test getting compliance history when empty."""
        mock_block = {'number': 100, 'transactions': []}
        compliance_manager.blockchain.w3.eth.get_block.return_value = mock_block

        history = compliance_manager.get_compliance_history()

        assert history == []

    def test_get_compliance_history_with_filters(self, compliance_manager):
        """Test getting compliance history with filters."""
        mock_block = {'number': 100, 'transactions': []}
        compliance_manager.blockchain.w3.eth.get_block.return_value = mock_block

        history = compliance_manager.get_compliance_history(filters=['data_share'])

        assert isinstance(history, list)
