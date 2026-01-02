import pytest
import sys
import os
import json
import tempfile
import time
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'datamgmtnode'))

from network.p2p_network import P2PNetwork, PeerInfo


class TestPeerInfo:
    """Tests for PeerInfo dataclass."""

    def test_peer_info_creation(self):
        """Test creating a PeerInfo instance."""
        peer = PeerInfo(host='192.168.1.1', port=8000)
        assert peer.host == '192.168.1.1'
        assert peer.port == 8000
        assert peer.node_id is None
        assert peer.failures == 0
        assert peer.successes == 0

    def test_success_rate_no_attempts(self):
        """Test success rate with no attempts."""
        peer = PeerInfo(host='localhost', port=8000)
        assert peer.success_rate == 0

    def test_success_rate_calculation(self):
        """Test success rate calculation."""
        peer = PeerInfo(host='localhost', port=8000, successes=7, failures=3)
        assert peer.success_rate == 0.7

    def test_is_healthy_recent_and_good_rate(self):
        """Test healthy peer detection."""
        peer = PeerInfo(
            host='localhost',
            port=8000,
            last_seen=time.time(),
            successes=5,
            failures=1
        )
        assert peer.is_healthy is True

    def test_is_healthy_old_peer(self):
        """Test unhealthy detection for old peer."""
        peer = PeerInfo(
            host='localhost',
            port=8000,
            last_seen=time.time() - 600,  # 10 minutes ago
            successes=5,
            failures=1
        )
        assert peer.is_healthy is False

    def test_is_healthy_new_peer_few_attempts(self):
        """Test new peer with few attempts is considered healthy."""
        peer = PeerInfo(
            host='localhost',
            port=8000,
            last_seen=time.time(),
            successes=1,
            failures=1
        )
        assert peer.is_healthy is True  # < 3 successes, so we give benefit of doubt


class TestP2PNetwork:
    """Tests for P2PNetwork class."""

    @pytest.fixture
    def mock_node(self):
        """Create a mock node."""
        node = Mock()
        node.config = Mock()
        node.config.node_id = 'test_node_1'
        node.encrypt_data = Mock(return_value='encrypted_data')
        node.decrypt_data = Mock(return_value='decrypted_data')
        node._hash_data = Mock(return_value='test_hash')
        node.data_manager = Mock()
        node.on_data_received = AsyncMock()
        return node

    @pytest.fixture
    def temp_data_dir(self):
        """Create a temporary data directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield tmpdir

    @pytest.fixture
    def p2p_network(self, mock_node, temp_data_dir):
        """Create a P2PNetwork instance."""
        return P2PNetwork(
            mock_node,
            8000,
            ['localhost:8001', 'localhost:8002'],
            temp_data_dir
        )

    def test_init(self, p2p_network, mock_node, temp_data_dir):
        """Test P2PNetwork initialization."""
        assert p2p_network.node == mock_node
        assert p2p_network.port == 8000
        assert len(p2p_network.bootstrap_peers) == 2
        assert p2p_network.data_dir == temp_data_dir
        assert p2p_network.server is None
        assert p2p_network._running is False

    def test_init_default_data_dir(self, mock_node):
        """Test P2PNetwork with default data dir."""
        network = P2PNetwork(mock_node, 8000)
        assert network.data_dir == './data'

    # =========================================================================
    # PEER PERSISTENCE TESTS
    # =========================================================================

    def test_save_and_load_peers(self, p2p_network, temp_data_dir):
        """Test saving and loading peers from disk."""
        # Add some peers
        p2p_network._known_peers[('192.168.1.1', 8000)] = PeerInfo(
            host='192.168.1.1',
            port=8000,
            node_id='node1',
            last_seen=time.time(),
            successes=5
        )
        p2p_network._known_peers[('192.168.1.2', 8001)] = PeerInfo(
            host='192.168.1.2',
            port=8001,
            node_id='node2',
            last_seen=time.time(),
            successes=3
        )

        # Save peers
        p2p_network._save_peers()

        # Verify file exists
        assert os.path.exists(p2p_network._peers_file)

        # Clear and reload
        p2p_network._known_peers.clear()
        p2p_network._load_peers()

        assert len(p2p_network._known_peers) == 2
        assert ('192.168.1.1', 8000) in p2p_network._known_peers

    def test_load_peers_no_file(self, p2p_network):
        """Test loading peers when no file exists."""
        p2p_network._load_peers()
        assert len(p2p_network._known_peers) == 0

    def test_save_excludes_old_peers(self, p2p_network, temp_data_dir):
        """Test that old peers are not saved."""
        # Add an old peer
        p2p_network._known_peers[('old.peer.com', 8000)] = PeerInfo(
            host='old.peer.com',
            port=8000,
            last_seen=time.time() - 100000  # Very old
        )
        # Add a recent peer
        p2p_network._known_peers[('new.peer.com', 8000)] = PeerInfo(
            host='new.peer.com',
            port=8000,
            last_seen=time.time()
        )

        p2p_network._save_peers()
        p2p_network._known_peers.clear()
        p2p_network._load_peers()

        # Only recent peer should be loaded
        assert len(p2p_network._known_peers) == 1
        assert ('new.peer.com', 8000) in p2p_network._known_peers

    # =========================================================================
    # BOOTSTRAP TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_start(self, p2p_network):
        """Test starting the P2P network."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            MockServer.return_value = mock_server
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.protocol = None

            await p2p_network.start()

            assert p2p_network.server is not None
            assert p2p_network._running is True
            mock_server.listen.assert_called_once_with(8000)

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    @pytest.mark.asyncio
    async def test_stop_saves_peers(self, p2p_network):
        """Test that stopping saves peers."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = Mock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.stop = Mock()
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()

            # Add a peer
            p2p_network._known_peers[('test.com', 8000)] = PeerInfo(
                host='test.com',
                port=8000,
                last_seen=time.time()
            )

            await p2p_network.stop()

            # Verify peers were saved
            assert os.path.exists(p2p_network._peers_file)

    def test_parse_peer_address_valid(self, p2p_network):
        """Test parsing valid peer addresses."""
        assert p2p_network._parse_peer_address('localhost:8000') == ('localhost', 8000)
        assert p2p_network._parse_peer_address('http://example.com:9000') == ('example.com', 9000)
        assert p2p_network._parse_peer_address('https://secure.com:443') == ('secure.com', 443)

    def test_parse_peer_address_invalid(self, p2p_network):
        """Test parsing invalid peer addresses."""
        assert p2p_network._parse_peer_address('invalid') is None
        assert p2p_network._parse_peer_address('') is None

    # =========================================================================
    # HEALTH MONITORING TESTS
    # =========================================================================

    def test_prune_dead_peers(self, p2p_network):
        """Test pruning dead peers."""
        # Add a dead peer
        p2p_network._known_peers[('dead.peer.com', 8000)] = PeerInfo(
            host='dead.peer.com',
            port=8000,
            last_seen=time.time() - 100000,
            failures=10,
            successes=0
        )
        # Add a healthy peer
        p2p_network._known_peers[('alive.peer.com', 8000)] = PeerInfo(
            host='alive.peer.com',
            port=8000,
            last_seen=time.time(),
            successes=5
        )

        p2p_network._prune_dead_peers()

        assert ('dead.peer.com', 8000) not in p2p_network._known_peers
        assert ('alive.peer.com', 8000) in p2p_network._known_peers

    @pytest.mark.asyncio
    async def test_check_peer_health_success(self, p2p_network):
        """Test successful health check."""
        peer_info = PeerInfo(host='localhost', port=8000)

        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.stop = Mock()
            MockServer.return_value = mock_server

            await p2p_network._check_peer_health('localhost', 8000, peer_info)

            assert peer_info.successes == 1
            assert peer_info.last_seen > 0
            assert peer_info.latency_ms > 0

    @pytest.mark.asyncio
    async def test_check_peer_health_timeout(self, p2p_network):
        """Test health check timeout."""
        peer_info = PeerInfo(host='localhost', port=8000)

        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.bootstrap = AsyncMock(side_effect=asyncio.TimeoutError())
            MockServer.return_value = mock_server

            await p2p_network._check_peer_health('localhost', 8000, peer_info)

            assert peer_info.failures == 1

    # =========================================================================
    # PEER EXCHANGE TESTS
    # =========================================================================

    def test_get_shareable_peer_list(self, p2p_network):
        """Test getting shareable peer list."""
        # Add healthy peer
        p2p_network._known_peers[('healthy.com', 8000)] = PeerInfo(
            host='healthy.com',
            port=8000,
            node_id='node1',
            last_seen=time.time(),
            successes=5
        )
        # Add unhealthy peer
        p2p_network._known_peers[('unhealthy.com', 8000)] = PeerInfo(
            host='unhealthy.com',
            port=8000,
            last_seen=time.time() - 600
        )

        peers = p2p_network._get_shareable_peer_list()

        assert len(peers) == 1
        assert peers[0]['host'] == 'healthy.com'

    def test_merge_peer_list(self, p2p_network):
        """Test merging peer list from exchange."""
        peer_list = [
            {'host': 'new1.com', 'port': 8000, 'node_id': 'n1'},
            {'host': 'new2.com', 'port': 8001, 'node_id': 'n2'},
        ]

        p2p_network._merge_peer_list(peer_list)

        assert len(p2p_network._known_peers) == 2
        assert ('new1.com', 8000) in p2p_network._known_peers
        assert ('new2.com', 8001) in p2p_network._known_peers

    def test_merge_peer_list_ignores_invalid(self, p2p_network):
        """Test that invalid peers are ignored during merge."""
        peer_list = [
            {'host': 'valid.com', 'port': 8000},
            {'host': None, 'port': 8000},  # Invalid
            {'port': 8000},  # Missing host
        ]

        p2p_network._merge_peer_list(peer_list)

        assert len(p2p_network._known_peers) == 1

    # =========================================================================
    # DATA OPERATIONS TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_send_data(self, p2p_network):
        """Test sending data to the network."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.set = AsyncMock()
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()
            await p2p_network.send_data('test_hash', 'test_data')

            mock_server.set.assert_called_once()
            p2p_network.node.encrypt_data.assert_called_once_with('test_data')

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    @pytest.mark.asyncio
    async def test_send_data_not_started(self, p2p_network):
        """Test sending data when network not started."""
        with pytest.raises(RuntimeError, match="P2P network not started"):
            await p2p_network.send_data('hash', 'data')

    @pytest.mark.asyncio
    async def test_get_data_found(self, p2p_network):
        """Test retrieving data from the network."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.get = AsyncMock(return_value=json.dumps({
                'hash': 'test_hash',
                'data': 'encrypted_data',
                'node_id': 'node1',
                'timestamp': time.time()
            }))
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()
            result = await p2p_network.get_data('test_hash')

            assert result == 'decrypted_data'

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    @pytest.mark.asyncio
    async def test_get_data_not_found(self, p2p_network):
        """Test retrieving non-existent data."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.get = AsyncMock(return_value=None)
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()
            result = await p2p_network.get_data('nonexistent')

            assert result is None

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    # =========================================================================
    # PEER MANAGEMENT API TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_connect_to_peer(self, p2p_network):
        """Test connecting to a new peer."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()
            await p2p_network.connect_to_peer('newpeer.com:9000')

            assert ('newpeer.com', 9000) in p2p_network._known_peers

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    @pytest.mark.asyncio
    async def test_connect_to_peer_invalid(self, p2p_network):
        """Test connecting with invalid peer format."""
        with patch('network.p2p_network.Server') as MockServer:
            mock_server = AsyncMock()
            mock_server.listen = AsyncMock()
            mock_server.bootstrap = AsyncMock()
            mock_server.protocol = None
            MockServer.return_value = mock_server

            await p2p_network.start()

            with pytest.raises(ValueError, match="Invalid peer format"):
                await p2p_network.connect_to_peer('invalid_address')

            # Cleanup
            p2p_network._running = False
            for task in p2p_network._background_tasks:
                task.cancel()

    def test_get_connected_peers(self, p2p_network):
        """Test getting connected peers list."""
        p2p_network._known_peers[('peer1.com', 8000)] = PeerInfo(
            host='peer1.com',
            port=8000,
            node_id='n1',
            last_seen=time.time(),
            latency_ms=50,
            successes=5
        )

        peers = p2p_network.get_connected_peers()

        assert len(peers) == 1
        assert peers[0]['host'] == 'peer1.com'
        assert peers[0]['latency_ms'] == 50
        assert 'healthy' in peers[0]

    def test_get_healthy_peers(self, p2p_network):
        """Test getting only healthy peers."""
        p2p_network._known_peers[('healthy.com', 8000)] = PeerInfo(
            host='healthy.com',
            port=8000,
            last_seen=time.time(),
            successes=5
        )
        p2p_network._known_peers[('unhealthy.com', 8000)] = PeerInfo(
            host='unhealthy.com',
            port=8000,
            last_seen=time.time() - 600
        )

        healthy = p2p_network.get_healthy_peers()

        assert len(healthy) == 1
        assert healthy[0]['host'] == 'healthy.com'

    def test_get_network_stats(self, p2p_network):
        """Test getting network statistics."""
        p2p_network._known_peers[('peer1.com', 8000)] = PeerInfo(
            host='peer1.com',
            port=8000,
            last_seen=time.time(),
            latency_ms=50,
            successes=5
        )

        stats = p2p_network.get_network_stats()

        assert stats['total_peers'] == 1
        assert stats['healthy_peers'] == 1
        assert stats['bootstrap_nodes'] == 2
        assert stats['avg_latency_ms'] == 50

    def test_is_running_property(self, p2p_network):
        """Test is_running property."""
        assert p2p_network.is_running is False

    # =========================================================================
    # INCOMING DATA HANDLING TESTS
    # =========================================================================

    @pytest.mark.asyncio
    async def test_handle_incoming_data_valid(self, p2p_network):
        """Test handling valid incoming data."""
        data = {'hash': 'test_hash', 'data': 'encrypted_data'}

        await p2p_network._handle_incoming_data(data)

        p2p_network.node.decrypt_data.assert_called_once()
        p2p_network.node.data_manager.store_data.assert_called_once()
        p2p_network.node.on_data_received.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_incoming_data_hash_mismatch(self, p2p_network):
        """Test handling data with hash mismatch."""
        p2p_network.node._hash_data = Mock(return_value='different_hash')

        data = {'hash': 'test_hash', 'data': 'encrypted_data'}

        await p2p_network._handle_incoming_data(data)

        p2p_network.node.data_manager.store_data.assert_not_called()

    @pytest.mark.asyncio
    async def test_handle_incoming_data_invalid(self, p2p_network):
        """Test handling invalid incoming data."""
        await p2p_network._handle_incoming_data(None)
        await p2p_network._handle_incoming_data({})
        await p2p_network._handle_incoming_data({'hash': 'test'})

        p2p_network.node.decrypt_data.assert_not_called()
