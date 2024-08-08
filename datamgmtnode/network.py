import asyncio
from pygundb import Gun

class P2PNetwork:
    def __init__(self, node, port, peers=None):
        self.node = node
        self.port = port
        self.gun = None
        self.initial_peers = peers or []

    async def start(self):
        self.gun = Gun(port=self.port, peers=self.initial_peers)
        await self.gun.start()
        print(f"P2P network started on port {self.port}")

        # Set up data sync
        self.gun.on('data_share', self._handle_incoming_data)

    async def stop(self):
        if self.gun:
            await self.gun.stop()

    async def send_data(self, data_hash, data):
        # Encrypt data before sending
        encrypted_data = self.node.encrypt_data(data)
        
        # Store data in Gun
        await self.gun.set('data_share', {
            'hash': data_hash,
            'data': encrypted_data,
            'timestamp': asyncio.get_event_loop().time()
        })

    async def _handle_incoming_data(self, data):
        if data and 'hash' in data and 'data' in data:
            # Decrypt the incoming data
            decrypted_data = self.node.decrypt_data(data['data'])
            
            # Verify the data hash
            if self.node._hash_data(decrypted_data) == data['hash']:
                # Store the data locally
                self.node.data_manager.store_data(data['hash'], decrypted_data)
                
                # Trigger any necessary events or callbacks
                await self.node.on_data_received(data['hash'], decrypted_data)
            else:
                print(f"Received data with hash mismatch: {data['hash']}")

    async def get_data(self, data_hash):
        data = await self.gun.get('data_share').get(data_hash).once()
        if data:
            return self.node.decrypt_data(data['data'])
        return None

    async def connect_to_peer(self, peer_url):
        await self.gun.add_peer(peer_url)
        print(f"Connected to peer: {peer_url}")

    def get_connected_peers(self):
        return self.gun.peers