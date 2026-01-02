import pytest
import sys
import os

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.data_manager import DataManager


class TestDataManager:
    def test_init_creates_database(self, temp_db_path):
        """Test that DataManager initializes a database."""
        dm = DataManager(temp_db_path)
        assert dm.db is not None
        dm.close()

    def test_store_and_get_data(self, temp_db_path):
        """Test storing and retrieving data."""
        dm = DataManager(temp_db_path)

        dm.store_data('test_key', 'test_value')
        result = dm.get_data('test_key')

        assert result == 'test_value'
        dm.close()

    def test_store_bytes_data(self, temp_db_path):
        """Test storing and retrieving bytes data."""
        dm = DataManager(temp_db_path)

        dm.store_data(b'binary_key', b'binary_value')
        result = dm.get_data(b'binary_key')

        assert result == 'binary_value'
        dm.close()

    def test_get_nonexistent_key(self, temp_db_path):
        """Test retrieving a non-existent key returns None."""
        dm = DataManager(temp_db_path)

        result = dm.get_data('nonexistent')

        assert result is None
        dm.close()

    def test_delete_data(self, temp_db_path):
        """Test deleting data."""
        dm = DataManager(temp_db_path)

        dm.store_data('delete_me', 'value')
        dm.delete_data('delete_me')
        result = dm.get_data('delete_me')

        assert result is None
        dm.close()

    def test_update_existing_key(self, temp_db_path):
        """Test updating an existing key."""
        dm = DataManager(temp_db_path)

        dm.store_data('key', 'original')
        dm.store_data('key', 'updated')
        result = dm.get_data('key')

        assert result == 'updated'
        dm.close()

    def test_context_manager(self, temp_db_path):
        """Test DataManager works as context manager."""
        with DataManager(temp_db_path) as dm:
            dm.store_data('ctx_key', 'ctx_value')
            assert dm.get_data('ctx_key') == 'ctx_value'

    def test_multiple_keys(self, temp_db_path):
        """Test storing multiple keys."""
        dm = DataManager(temp_db_path)

        dm.store_data('key1', 'value1')
        dm.store_data('key2', 'value2')
        dm.store_data('key3', 'value3')

        assert dm.get_data('key1') == 'value1'
        assert dm.get_data('key2') == 'value2'
        assert dm.get_data('key3') == 'value3'
        dm.close()
