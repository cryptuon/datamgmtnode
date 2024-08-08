import asyncio
from node import Node, NodeConfig

async def main():
    config = NodeConfig(
        blockchain_type='evm',
        blockchain_url='https://mainnet.infura.io/v3/YOUR-PROJECT-ID',
        private_key='your_private_key_here',
        native_token_address='0x...',
        db_path='./data/nodedb',
        sqlite_db_path='./data/sqlite.db',
        p2p_port=8000,
        plugin_dir='./plugins',
        node_id='node1',
        node_signature='signature_here',
        initial_peers=['http://peer1.example.com', 'http://peer2.example.com']
    )

    node = Node(config)
    
    try:
        await node.start()
        print("Node started successfully")
        # Keep the node running
        while True:
            await asyncio.sleep(1)
    except KeyboardInterrupt:
        print("Shutting down node...")
    finally:
        await node.stop()

if __name__ == "__main__":
    asyncio.run(main())