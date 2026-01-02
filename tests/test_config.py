import pytest
import sys
import os
import tempfile

# Add parent directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from services.node import NodeConfig, ConfigurationError


class TestNodeConfigValidation:
    """Tests for NodeConfig validation."""

    def get_valid_config(self, **overrides):
        """Get a valid config dict with optional overrides."""
        defaults = {
            'blockchain_type': 'evm',
            'blockchain_url': 'https://mainnet.infura.io/v3/test',
            'private_key': 'test_private_key',
            'native_token_address': '0x0000000000000000000000000000000000000000',
            'db_path': tempfile.mkdtemp(),
            'sqlite_db_path': os.path.join(tempfile.mkdtemp(), 'test.db'),
            'p2p_port': 8000,
            'plugin_dir': './plugins',
            'node_id': 'test_node',
            'node_signature': 'test_signature',
            'initial_peers': [],
            'data_dir': tempfile.mkdtemp()
        }
        defaults.update(overrides)
        return defaults

    def test_valid_config(self):
        config_dict = self.get_valid_config()
        config = NodeConfig(**config_dict)
        assert config.validate() is True

    def test_invalid_blockchain_type(self):
        config_dict = self.get_valid_config(blockchain_type='solana')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'blockchain_type' in str(exc.value)

    def test_missing_blockchain_url(self):
        config_dict = self.get_valid_config(blockchain_url='')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'blockchain_url is required' in str(exc.value)

    def test_invalid_blockchain_url_protocol(self):
        config_dict = self.get_valid_config(blockchain_url='ftp://example.com')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'http' in str(exc.value)

    def test_valid_blockchain_url_protocols(self):
        for url in ['http://example.com', 'https://example.com',
                    'ws://example.com', 'wss://example.com']:
            config_dict = self.get_valid_config(blockchain_url=url)
            config = NodeConfig(**config_dict)
            assert config.validate() is True

    def test_invalid_native_token_address(self):
        config_dict = self.get_valid_config(native_token_address='not_an_address')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'native_token_address' in str(exc.value)

    def test_valid_native_token_address_null(self):
        # Empty string should pass (some chains might not use this)
        config_dict = self.get_valid_config(native_token_address='')
        config = NodeConfig(**config_dict)
        # Empty string passes the regex check (it doesn't match the pattern but isn't checked)
        assert config.validate() is True

    def test_invalid_port_too_low(self):
        config_dict = self.get_valid_config(p2p_port=0)
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'p2p_port' in str(exc.value)

    def test_invalid_port_too_high(self):
        config_dict = self.get_valid_config(p2p_port=70000)
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'p2p_port' in str(exc.value)

    def test_invalid_port_not_int(self):
        config_dict = self.get_valid_config(p2p_port='8000')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'p2p_port' in str(exc.value)

    def test_valid_port_boundaries(self):
        for port in [1, 80, 8080, 65535]:
            config_dict = self.get_valid_config(p2p_port=port)
            config = NodeConfig(**config_dict)
            assert config.validate() is True

    def test_missing_node_id(self):
        config_dict = self.get_valid_config(node_id='')
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'node_id' in str(exc.value)

    def test_node_id_too_long(self):
        config_dict = self.get_valid_config(node_id='x' * 101)
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'node_id' in str(exc.value)
        assert '100 characters' in str(exc.value)

    def test_invalid_peer_url(self):
        config_dict = self.get_valid_config(
            initial_peers=['http://valid.com', 'ftp://invalid.com']
        )
        config = NodeConfig(**config_dict)
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        assert 'ftp://invalid.com' in str(exc.value)

    def test_valid_peer_urls(self):
        config_dict = self.get_valid_config(
            initial_peers=['http://peer1.com:8000', 'https://peer2.com:8001']
        )
        config = NodeConfig(**config_dict)
        assert config.validate() is True

    def test_empty_peers_list_is_valid(self):
        config_dict = self.get_valid_config(initial_peers=[])
        config = NodeConfig(**config_dict)
        assert config.validate() is True

    def test_data_dir_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, 'new_data_dir')
            config_dict = self.get_valid_config(data_dir=new_dir)
            config = NodeConfig(**config_dict)
            config.validate()
            assert os.path.exists(new_dir)

    def test_db_path_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            new_dir = os.path.join(tmpdir, 'new_db')
            config_dict = self.get_valid_config(db_path=new_dir)
            config = NodeConfig(**config_dict)
            config.validate()
            assert os.path.exists(new_dir)

    def test_sqlite_db_dir_created(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            sqlite_path = os.path.join(tmpdir, 'subdir', 'test.db')
            config_dict = self.get_valid_config(sqlite_db_path=sqlite_path)
            config = NodeConfig(**config_dict)
            config.validate()
            assert os.path.exists(os.path.dirname(sqlite_path))

    def test_multiple_errors_reported(self):
        config = NodeConfig(
            blockchain_type='invalid',
            blockchain_url='',
            private_key='',
            native_token_address='invalid',
            db_path='/tmp/test',
            sqlite_db_path='/tmp/test.db',
            p2p_port=0,
            plugin_dir='./plugins',
            node_id='',
            node_signature='',
            initial_peers=['ftp://bad.url'],
            data_dir='/tmp'
        )
        with pytest.raises(ConfigurationError) as exc:
            config.validate()
        error_msg = str(exc.value)
        # Should contain multiple errors
        assert 'blockchain_type' in error_msg
        assert 'blockchain_url' in error_msg
        assert 'p2p_port' in error_msg
        assert 'node_id' in error_msg


class TestNodeConfigDefaults:
    """Tests for NodeConfig defaults."""

    def test_data_dir_default(self):
        config = NodeConfig(
            blockchain_type='evm',
            blockchain_url='https://example.com',
            private_key='key',
            native_token_address='0x0000000000000000000000000000000000000000',
            db_path='/tmp/db',
            sqlite_db_path='/tmp/test.db',
            p2p_port=8000,
            plugin_dir='./plugins',
            node_id='node1',
            node_signature='sig',
            initial_peers=[]
        )
        assert config.data_dir == './data'

    def test_data_dir_explicit(self):
        config = NodeConfig(
            blockchain_type='evm',
            blockchain_url='https://example.com',
            private_key='key',
            native_token_address='0x0000000000000000000000000000000000000000',
            db_path='/tmp/db',
            sqlite_db_path='/tmp/test.db',
            p2p_port=8000,
            plugin_dir='./plugins',
            node_id='node1',
            node_signature='sig',
            initial_peers=[],
            data_dir='/custom/data'
        )
        assert config.data_dir == '/custom/data'
