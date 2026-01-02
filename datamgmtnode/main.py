import argparse
import asyncio
import os
import signal
import logging
from dotenv import load_dotenv
from services.node import Node, NodeConfig, ConfigurationError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Shutdown timeout in seconds
SHUTDOWN_TIMEOUT = 30


def load_config():
    """Load configuration from environment variables."""
    load_dotenv()

    initial_peers_str = os.getenv('INITIAL_PEERS', '')
    initial_peers = [p.strip() for p in initial_peers_str.split(',') if p.strip()]

    return NodeConfig(
        blockchain_type=os.getenv('BLOCKCHAIN_TYPE', 'evm'),
        blockchain_url=os.getenv('BLOCKCHAIN_URL', 'https://mainnet.infura.io/v3/YOUR-PROJECT-ID'),
        private_key=os.getenv('PRIVATE_KEY', ''),
        native_token_address=os.getenv('NATIVE_TOKEN_ADDRESS', '0x0000000000000000000000000000000000000000'),
        db_path=os.getenv('DB_PATH', './data/nodedb'),
        sqlite_db_path=os.getenv('SQLITE_DB_PATH', './data/sqlite.db'),
        p2p_port=int(os.getenv('P2P_PORT', '8000')),
        plugin_dir=os.getenv('PLUGIN_DIR', './plugins'),
        node_id=os.getenv('NODE_ID', 'node1'),
        node_signature=os.getenv('NODE_SIGNATURE', ''),
        initial_peers=initial_peers,
        data_dir=os.getenv('DATA_DIR', './data')
    )


async def shutdown(node, loop, signal_received=None):
    """Graceful shutdown with timeout."""
    if signal_received:
        logger.info(f"Received exit signal {signal_received.name}...")

    logger.info("Shutting down node...")

    try:
        # Use asyncio.wait_for to enforce shutdown timeout
        await asyncio.wait_for(node.stop(), timeout=SHUTDOWN_TIMEOUT)
        logger.info("Node stopped gracefully.")
    except asyncio.TimeoutError:
        logger.warning(f"Shutdown timed out after {SHUTDOWN_TIMEOUT}s, forcing exit...")
    except Exception as e:
        logger.error(f"Error during shutdown: {e}")

    # Cancel all remaining tasks
    tasks = [t for t in asyncio.all_tasks(loop) if t is not asyncio.current_task()]
    for task in tasks:
        task.cancel()

    if tasks:
        logger.info(f"Cancelling {len(tasks)} outstanding tasks...")
        await asyncio.gather(*tasks, return_exceptions=True)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description='DataMgmt Node - Decentralized data management system'
    )
    parser.add_argument(
        '--tui',
        action='store_true',
        help='Launch the Terminal User Interface instead of server mode'
    )
    parser.add_argument(
        '--no-dashboard',
        action='store_true',
        help='Disable the web dashboard API'
    )
    parser.add_argument(
        '--api-url',
        type=str,
        default='http://localhost:8082',
        help='Dashboard API URL for TUI mode (default: http://localhost:8082)'
    )
    return parser.parse_args()


async def run_server(config, enable_dashboard: bool = True):
    """Run the node in server mode."""
    node = Node(config, enable_dashboard=enable_dashboard)
    loop = asyncio.get_running_loop()
    shutdown_event = asyncio.Event()

    # Setup signal handlers for graceful shutdown
    def signal_handler(sig):
        logger.info(f"Received signal {sig.name}")
        shutdown_event.set()

    # Register signal handlers (Unix-only)
    for sig in (signal.SIGTERM, signal.SIGINT):
        try:
            loop.add_signal_handler(sig, lambda s=sig: signal_handler(s))
        except NotImplementedError:
            # Windows doesn't support add_signal_handler
            signal.signal(sig, lambda s, f, sig=sig: signal_handler(sig))

    try:
        await node.start()
        logger.info("Node started successfully")
        logger.info(f"  - Internal API: http://localhost:8080")
        logger.info(f"  - External API: http://0.0.0.0:8081")
        if enable_dashboard:
            logger.info(f"  - Dashboard:    http://localhost:8082")
        logger.info(f"  - P2P Port:     {config.p2p_port}")
        logger.info("Press Ctrl+C to stop the node")

        # Wait for shutdown signal
        await shutdown_event.wait()

    except Exception as e:
        logger.error(f"Unexpected error: {e}")
    finally:
        await shutdown(node, loop)


def run_tui(api_url: str):
    """Run the Terminal User Interface."""
    try:
        from tui.app import DataMgmtTUI
    except ImportError:
        logger.error("TUI dependencies not installed. Run: poetry install")
        return

    logger.info(f"Starting TUI, connecting to {api_url}")
    app = DataMgmtTUI(api_url=api_url)
    app.run()


async def main():
    args = parse_args()
    config = load_config()

    # Validate configuration before starting
    try:
        config.validate()
        logger.info("Configuration validated successfully")
    except ConfigurationError as e:
        logger.error(f"Configuration error: {e}")
        return

    if not config.private_key:
        logger.warning("No private key configured. Set PRIVATE_KEY in .env file.")

    if args.tui:
        # Run in TUI mode
        run_tui(args.api_url)
    else:
        # Run in server mode
        enable_dashboard = not args.no_dashboard
        await run_server(config, enable_dashboard=enable_dashboard)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
