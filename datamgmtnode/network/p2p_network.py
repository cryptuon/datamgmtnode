import asyncio
import json
import logging
import os
import time
from dataclasses import dataclass, asdict
from typing import Optional
from kademlia.network import Server

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


@dataclass
class PeerInfo:
    """Information about a peer node."""
    host: str
    port: int
    node_id: Optional[str] = None
    last_seen: float = 0
    latency_ms: float = 0
    failures: int = 0
    successes: int = 0

    @property
    def success_rate(self) -> float:
        total = self.failures + self.successes
        return self.successes / total if total > 0 else 0

    @property
    def is_healthy(self) -> bool:
        """Peer is healthy if seen recently and has good success rate."""
        age = time.time() - self.last_seen
        return age < 300 and (self.success_rate > 0.5 or self.successes < 3)


class P2PNetwork:
    """
    P2P Network implementation using Kademlia DHT.

    Features:
    - Decentralized key-value storage via DHT
    - Automatic peer discovery
    - Persistent peer storage
    - Health monitoring and automatic re-bootstrap
    - Peer exchange protocol
    """

    def __init__(self, node, port, peers=None, data_dir=None):
        self.node = node
        self.port = port
        self.bootstrap_peers = peers or []
        self.data_dir = data_dir or './data'
        self.server = None
        self._running = False

        # Peer management
        self._known_peers: dict[tuple, PeerInfo] = {}
        self._peers_file = os.path.join(self.data_dir, 'known_peers.json')

        # Background tasks
        self._background_tasks = []
        self._health_check_interval = 60  # seconds
        self._peer_exchange_interval = 120  # seconds
        self._rebootstrap_interval = 300  # seconds
        self._min_peers = 3  # minimum peers before re-bootstrap

    async def start(self):
        """Start the P2P network server."""
        # Ensure data directory exists
        os.makedirs(self.data_dir, exist_ok=True)

        # Load previously known peers
        self._load_peers()

        # Start Kademlia server
        self.server = Server()
        await self.server.listen(self.port)
        self._running = True
        logger.info(f"P2P network started on port {self.port}")

        # Bootstrap to network
        await self._bootstrap()

        # Start background tasks
        self._start_background_tasks()

    def _start_background_tasks(self):
        """Start background maintenance tasks."""
        self._background_tasks = [
            asyncio.create_task(self._health_check_loop()),
            asyncio.create_task(self._peer_exchange_loop()),
            asyncio.create_task(self._rebootstrap_loop()),
        ]

    async def stop(self):
        """Stop the P2P network server."""
        self._running = False

        # Cancel background tasks
        for task in self._background_tasks:
            task.cancel()
            try:
                await task
            except asyncio.CancelledError:
                pass

        # Save known peers
        self._save_peers()

        # Stop server
        if self.server:
            self.server.stop()
            logger.info("P2P network stopped")

    # =========================================================================
    # PEER PERSISTENCE
    # =========================================================================

    def _load_peers(self):
        """Load known peers from disk."""
        if not os.path.exists(self._peers_file):
            logger.info("No saved peers found, starting fresh")
            return

        try:
            with open(self._peers_file, 'r') as f:
                data = json.load(f)

            for peer_data in data:
                peer = PeerInfo(**peer_data)
                key = (peer.host, peer.port)
                self._known_peers[key] = peer

            logger.info(f"Loaded {len(self._known_peers)} peers from disk")

        except (json.JSONDecodeError, IOError) as e:
            logger.warning(f"Failed to load peers: {e}")

    def _save_peers(self):
        """Save known peers to disk."""
        try:
            # Only save healthy peers seen in last 24 hours
            cutoff = time.time() - 86400
            peers_to_save = [
                asdict(peer) for peer in self._known_peers.values()
                if peer.last_seen > cutoff
            ]

            with open(self._peers_file, 'w') as f:
                json.dump(peers_to_save, f, indent=2)

            logger.info(f"Saved {len(peers_to_save)} peers to disk")

        except IOError as e:
            logger.error(f"Failed to save peers: {e}")

    # =========================================================================
    # BOOTSTRAP & DISCOVERY
    # =========================================================================

    async def _bootstrap(self):
        """Connect to bootstrap nodes and known peers."""
        bootstrap_nodes = []

        # Add configured bootstrap peers
        for peer in self.bootstrap_peers:
            parsed = self._parse_peer_address(peer)
            if parsed:
                bootstrap_nodes.append(parsed)

        # Add previously known healthy peers
        for (host, port), peer_info in self._known_peers.items():
            if peer_info.is_healthy:
                bootstrap_nodes.append((host, port))

        if not bootstrap_nodes:
            logger.warning("No bootstrap nodes available")
            return

        # Deduplicate
        bootstrap_nodes = list(set(bootstrap_nodes))
        logger.info(f"Bootstrapping to {len(bootstrap_nodes)} node(s)")

        try:
            await self.server.bootstrap(bootstrap_nodes)

            # Update known peers from routing table
            self._update_known_peers_from_routing_table()

            logger.info(f"Bootstrap complete, {len(self._known_peers)} peers known")

        except Exception as e:
            logger.error(f"Bootstrap failed: {e}")

    async def _rebootstrap_loop(self):
        """Periodically re-bootstrap if peer count is low."""
        while self._running:
            await asyncio.sleep(self._rebootstrap_interval)

            if not self._running:
                break

            active_peers = self._count_active_peers()

            if active_peers < self._min_peers:
                logger.info(f"Only {active_peers} active peers, re-bootstrapping...")
                await self._bootstrap()

    def _count_active_peers(self) -> int:
        """Count peers in the routing table."""
        if not self.server or not self.server.protocol:
            return 0

        count = 0
        for bucket in self.server.protocol.router.buckets:
            count += len(bucket.get_nodes())
        return count

    def _parse_peer_address(self, peer: str) -> Optional[tuple]:
        """Parse peer address string to (host, port) tuple."""
        try:
            peer_clean = peer.replace("http://", "").replace("https://", "")
            if ":" in peer_clean:
                host, port_str = peer_clean.rsplit(":", 1)
                return (host, int(port_str))
        except (ValueError, AttributeError) as e:
            logger.warning(f"Invalid peer address '{peer}': {e}")
        return None

    # =========================================================================
    # HEALTH MONITORING
    # =========================================================================

    async def _health_check_loop(self):
        """Periodically check peer health."""
        while self._running:
            await asyncio.sleep(self._health_check_interval)

            if not self._running:
                break

            await self._check_all_peers_health()

    async def _check_all_peers_health(self):
        """Check health of all known peers."""
        self._update_known_peers_from_routing_table()

        tasks = []
        for (host, port), peer_info in list(self._known_peers.items()):
            tasks.append(self._check_peer_health(host, port, peer_info))

        if tasks:
            await asyncio.gather(*tasks, return_exceptions=True)

        # Remove dead peers (not seen in 24 hours with high failure rate)
        self._prune_dead_peers()

    async def _check_peer_health(self, host: str, port: int, peer_info: PeerInfo):
        """Check health of a single peer by pinging it."""
        start_time = time.time()

        try:
            # Try to connect and query the peer
            test_server = Server()
            await asyncio.wait_for(
                test_server.bootstrap([(host, port)]),
                timeout=5.0
            )
            test_server.stop()

            # Success
            latency = (time.time() - start_time) * 1000
            peer_info.last_seen = time.time()
            peer_info.latency_ms = latency
            peer_info.successes += 1

            logger.debug(f"Peer {host}:{port} healthy (latency: {latency:.0f}ms)")

        except asyncio.TimeoutError:
            peer_info.failures += 1
            logger.debug(f"Peer {host}:{port} timeout")

        except Exception as e:
            peer_info.failures += 1
            logger.debug(f"Peer {host}:{port} failed: {e}")

    def _prune_dead_peers(self):
        """Remove peers that have been unresponsive."""
        cutoff = time.time() - 86400  # 24 hours
        dead_peers = []

        for key, peer_info in self._known_peers.items():
            if peer_info.last_seen < cutoff and peer_info.success_rate < 0.1:
                dead_peers.append(key)

        for key in dead_peers:
            del self._known_peers[key]
            logger.info(f"Pruned dead peer {key[0]}:{key[1]}")

    def _update_known_peers_from_routing_table(self):
        """Update known peers from Kademlia routing table."""
        if not self.server or not self.server.protocol:
            return

        for bucket in self.server.protocol.router.buckets:
            for node in bucket.get_nodes():
                key = (node.ip, node.port)
                if key not in self._known_peers:
                    self._known_peers[key] = PeerInfo(
                        host=node.ip,
                        port=node.port,
                        node_id=node.id.hex() if node.id else None,
                        last_seen=time.time()
                    )
                else:
                    self._known_peers[key].last_seen = time.time()
                    if node.id:
                        self._known_peers[key].node_id = node.id.hex()

    # =========================================================================
    # PEER EXCHANGE
    # =========================================================================

    async def _peer_exchange_loop(self):
        """Periodically exchange peer lists with known peers."""
        while self._running:
            await asyncio.sleep(self._peer_exchange_interval)

            if not self._running:
                break

            await self._exchange_peers()

    async def _exchange_peers(self):
        """Share our peer list and receive peers from others."""
        # Store our peer list in DHT for others to discover
        peer_list = self._get_shareable_peer_list()

        if not peer_list:
            return

        try:
            # Store under a well-known key derived from our node ID
            exchange_key = f"peers:{self.node.config.node_id}"
            await self.server.set(exchange_key, json.dumps(peer_list))

            # Try to fetch peer lists from known nodes
            await self._fetch_peer_lists()

        except Exception as e:
            logger.debug(f"Peer exchange failed: {e}")

    def _get_shareable_peer_list(self) -> list:
        """Get list of healthy peers to share."""
        peers = []
        for (host, port), peer_info in self._known_peers.items():
            if peer_info.is_healthy:
                peers.append({
                    'host': host,
                    'port': port,
                    'node_id': peer_info.node_id
                })
        return peers[:20]  # Limit to 20 peers

    async def _fetch_peer_lists(self):
        """Fetch peer lists from known nodes."""
        for (host, port), peer_info in list(self._known_peers.items())[:10]:
            if not peer_info.node_id:
                continue

            try:
                exchange_key = f"peers:{peer_info.node_id}"
                data = await asyncio.wait_for(
                    self.server.get(exchange_key),
                    timeout=5.0
                )

                if data:
                    peer_list = json.loads(data)
                    self._merge_peer_list(peer_list)

            except (asyncio.TimeoutError, json.JSONDecodeError):
                pass
            except Exception as e:
                logger.debug(f"Failed to fetch peers from {host}:{port}: {e}")

    def _merge_peer_list(self, peer_list: list):
        """Merge received peer list into known peers."""
        for peer_data in peer_list:
            host = peer_data.get('host')
            port = peer_data.get('port')

            if not host or not port:
                continue

            key = (host, port)
            if key not in self._known_peers:
                self._known_peers[key] = PeerInfo(
                    host=host,
                    port=port,
                    node_id=peer_data.get('node_id'),
                    last_seen=0  # Not verified yet
                )
                logger.debug(f"Discovered new peer via exchange: {host}:{port}")

    # =========================================================================
    # DATA OPERATIONS
    # =========================================================================

    async def send_data(self, data_hash: str, data: str):
        """Store data in the DHT network."""
        if not self.server:
            raise RuntimeError("P2P network not started")

        encrypted_data = self.node.encrypt_data(data)

        payload = json.dumps({
            'hash': data_hash,
            'data': encrypted_data,
            'node_id': self.node.config.node_id,
            'timestamp': time.time()
        })

        await self.server.set(data_hash, payload)
        logger.info(f"Data stored in DHT: {data_hash[:16]}...")

    async def get_data(self, data_hash: str) -> Optional[str]:
        """Retrieve data from the DHT network."""
        if not self.server:
            raise RuntimeError("P2P network not started")

        try:
            payload = await self.server.get(data_hash)
            if payload is None:
                return None

            data_obj = json.loads(payload)
            encrypted_data = data_obj.get('data')

            if encrypted_data:
                decrypted = self.node.decrypt_data(encrypted_data)

                if self.node._hash_data(decrypted) == data_hash:
                    return decrypted
                else:
                    logger.warning(f"Hash mismatch: {data_hash[:16]}...")
                    return None

            return None

        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse DHT data: {e}")
            return None
        except Exception as e:
            logger.error(f"Failed to retrieve data: {e}")
            return None

    async def broadcast_data(self, data_hash: str, data: str):
        """Broadcast data to the network (alias for send_data)."""
        await self.send_data(data_hash, data)

    # =========================================================================
    # PEER MANAGEMENT API
    # =========================================================================

    async def connect_to_peer(self, peer_url: str):
        """Connect to a new peer."""
        if not self.server:
            raise RuntimeError("P2P network not started")

        parsed = self._parse_peer_address(peer_url)
        if not parsed:
            raise ValueError(f"Invalid peer format: {peer_url}")

        host, port = parsed

        try:
            await self.server.bootstrap([(host, port)])

            # Add to known peers
            key = (host, port)
            if key not in self._known_peers:
                self._known_peers[key] = PeerInfo(
                    host=host,
                    port=port,
                    last_seen=time.time()
                )
            else:
                self._known_peers[key].last_seen = time.time()
                self._known_peers[key].successes += 1

            logger.info(f"Connected to peer: {peer_url}")

        except Exception as e:
            logger.error(f"Failed to connect to {peer_url}: {e}")
            raise

    def get_connected_peers(self) -> list:
        """Get list of all known peers with health info."""
        peers = []
        for (host, port), peer_info in self._known_peers.items():
            peers.append({
                'host': host,
                'port': port,
                'node_id': peer_info.node_id,
                'last_seen': peer_info.last_seen,
                'latency_ms': peer_info.latency_ms,
                'success_rate': peer_info.success_rate,
                'healthy': peer_info.is_healthy
            })
        return sorted(peers, key=lambda p: -p['last_seen'])

    def get_healthy_peers(self) -> list:
        """Get only healthy peers."""
        return [p for p in self.get_connected_peers() if p['healthy']]

    def get_network_stats(self) -> dict:
        """Get network statistics."""
        peers = self.get_connected_peers()
        healthy = [p for p in peers if p['healthy']]

        return {
            'total_peers': len(peers),
            'healthy_peers': len(healthy),
            'active_peers': self._count_active_peers(),
            'bootstrap_nodes': len(self.bootstrap_peers),
            'avg_latency_ms': sum(p['latency_ms'] for p in healthy) / len(healthy) if healthy else 0
        }

    @property
    def is_running(self) -> bool:
        """Check if the P2P network is running."""
        return self._running

    async def _handle_incoming_data(self, data: dict):
        """Handle incoming data from the network."""
        if data and 'hash' in data and 'data' in data:
            try:
                decrypted_data = self.node.decrypt_data(data['data'])

                if self.node._hash_data(decrypted_data) == data['hash']:
                    self.node.data_manager.store_data(data['hash'], decrypted_data)
                    await self.node.on_data_received(data['hash'], decrypted_data)
                else:
                    logger.warning(f"Hash mismatch: {data['hash'][:16]}...")

            except Exception as e:
                logger.error(f"Error handling incoming data: {e}")
