"""Dashboard API for serving Vue.js static files and WebSocket."""

import logging
import mimetypes
from pathlib import Path

import aiohttp.web

from datamgmtnode.api.validation import (
    ValidationError,
    validate_eth_address,
    validate_filters,
    validate_hash,
    validate_share_data_request,
    validate_transfer_request,
)
from datamgmtnode.api.websocket_handler import WebSocketManager
from datamgmtnode.dashboard.event_bus import EventBus

logger = logging.getLogger(__name__)


class DashboardAPI:
    """Dashboard API for TUI and web interface.

    Serves Vue.js static files and provides WebSocket for real-time updates.
    Also proxies API requests to the internal/external APIs for unified access.
    """

    def __init__(self, node, event_bus: EventBus, port: int = 8082):
        """Initialize Dashboard API.

        Args:
            node: The node instance.
            event_bus: Event bus for real-time updates.
            port: Port to serve on (default 8082).
        """
        self.node = node
        self.event_bus = event_bus
        self.port = port
        self.ws_manager = WebSocketManager(event_bus)
        self.runner = None

        # Path to static files (built Vue.js app)
        self.static_path = Path(__file__).parent.parent / 'dashboard' / 'static'

    async def start(self):
        """Start the Dashboard API server."""
        app = aiohttp.web.Application(middlewares=[self._error_middleware])

        # WebSocket endpoint
        app.router.add_get('/ws', self.ws_manager.handle_websocket)

        # API endpoints (proxy to node services)
        app.router.add_get('/api/health', self._handle_health)
        app.router.add_get('/api/balance/{address}', self._handle_balance)
        app.router.add_post('/api/transfer', self._handle_transfer)
        app.router.add_get('/api/tokens', self._handle_list_tokens)
        app.router.add_post('/api/tokens', self._handle_add_token)
        app.router.add_post('/api/share_data', self._handle_share_data)
        app.router.add_get('/api/data/{data_hash}', self._handle_get_data)
        app.router.add_get('/api/verify_data/{data_hash}', self._handle_verify_data)
        app.router.add_get('/api/compliance_history', self._handle_compliance_history)
        app.router.add_get('/api/network/stats', self._handle_network_stats)
        app.router.add_get('/api/network/peers', self._handle_network_peers)

        # Dashboard info endpoint
        app.router.add_get('/api/dashboard/info', self._handle_dashboard_info)

        # Serve static files if available
        if self.static_path.exists() and (self.static_path / 'index.html').exists():
            # Serve assets directory
            assets_path = self.static_path / 'assets'
            if assets_path.exists():
                app.router.add_static('/assets', assets_path)

            # Serve index.html for SPA routing (catch-all)
            app.router.add_get('/', self._serve_index)
            app.router.add_get('/{path:.*}', self._serve_static_or_index)
            logger.info(f"Serving Vue.js dashboard from {self.static_path}")
        else:
            app.router.add_get('/', self._handle_no_static)
            app.router.add_get('/{path:.*}', self._handle_no_static)
            logger.warning(
                f"Vue.js dashboard not found at {self.static_path}. "
                "Run 'python scripts/build_dashboard.py' to build it."
            )

        self.runner = aiohttp.web.AppRunner(app)
        await self.runner.setup()
        site = aiohttp.web.TCPSite(self.runner, '0.0.0.0', self.port)
        await site.start()
        logger.info(f"Dashboard API started on port {self.port}")

    async def stop(self):
        """Stop the Dashboard API server."""
        await self.ws_manager.close_all()
        if self.runner:
            await self.runner.cleanup()
            logger.info("Dashboard API stopped")

    @aiohttp.web.middleware
    async def _error_middleware(self, request, handler):
        """Global error handling middleware."""
        try:
            return await handler(request)
        except ValidationError as e:
            return aiohttp.web.json_response(
                {'error': e.message, 'field': e.field},
                status=422
            )
        except aiohttp.web.HTTPException:
            raise
        except Exception as e:
            logger.exception(f"Dashboard API error: {e}")
            return aiohttp.web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    # Static file handlers

    async def _serve_index(self, request):
        """Serve index.html."""
        index_path = self.static_path / 'index.html'
        return aiohttp.web.FileResponse(index_path)

    async def _serve_static_or_index(self, request):
        """Serve static file or fall back to index.html for SPA routing."""
        path = request.match_info['path']

        # Check if it's a static file
        file_path = self.static_path / path
        if file_path.exists() and file_path.is_file():
            # Determine content type
            content_type, _ = mimetypes.guess_type(str(file_path))
            return aiohttp.web.FileResponse(
                file_path,
                headers={'Content-Type': content_type or 'application/octet-stream'}
            )

        # Fall back to index.html for SPA routing
        return await self._serve_index(request)

    async def _handle_no_static(self, request):
        """Handle requests when static files are not available."""
        return aiohttp.web.json_response({
            'message': 'Dashboard API is running',
            'note': 'Vue.js dashboard not built. Run: python scripts/build_dashboard.py',
            'websocket': f'ws://localhost:{self.port}/ws',
            'api_prefix': '/api',
            'endpoints': [
                'GET /api/health',
                'GET /api/balance/{address}',
                'POST /api/transfer',
                'GET /api/tokens',
                'POST /api/tokens',
                'POST /api/share_data',
                'GET /api/data/{data_hash}',
                'GET /api/verify_data/{data_hash}',
                'GET /api/compliance_history',
                'GET /api/network/stats',
                'GET /api/network/peers',
                'GET /api/dashboard/info'
            ]
        })

    # API handlers (proxy to node services)

    async def _handle_health(self, request):
        """Get health status."""
        blockchain_connected = self.node.blockchain_interface.w3 is not None
        p2p_running = self.node.p2p_network.is_running

        status = 'healthy' if (blockchain_connected and p2p_running) else 'degraded'

        return aiohttp.web.json_response({
            'status': status,
            'components': {
                'blockchain': 'connected' if blockchain_connected else 'disconnected',
                'p2p_network': 'running' if p2p_running else 'stopped',
                'encryption': 'initialized',
            },
            'version': '0.1.0',
            'node_id': self.node.config.node_id
        })

    async def _handle_balance(self, request):
        """Get token balance for an address."""
        address = request.match_info['address']
        address = validate_eth_address(address, 'address')

        try:
            balance = self.node.token_manager.get_balance(
                address,
                self.node.get_native_token_address()
            )
            return aiohttp.web.json_response({
                'address': address,
                'balance': str(balance),
                'token': self.node.get_native_token_address()
            })
        except ValueError as e:
            return aiohttp.web.json_response(
                {'error': str(e)},
                status=400
            )

    async def _handle_transfer(self, request):
        """Transfer tokens between addresses."""
        try:
            data = await request.json()
        except Exception:
            raise ValidationError("Invalid JSON body")

        validated = validate_transfer_request(data)

        try:
            success, tx_hash = self.node.payment_processor.process_payment(
                validated.from_address,
                validated.to_address,
                validated.amount,
                validated.token
            )
            return aiohttp.web.json_response({
                'success': success,
                'tx_hash': tx_hash,
                'from': validated.from_address,
                'to': validated.to_address,
                'amount': str(validated.amount)
            }, status=200 if success else 400)
        except ValueError as e:
            return aiohttp.web.json_response(
                {'error': str(e)},
                status=400
            )

    async def _handle_list_tokens(self, request):
        """List all supported tokens."""
        tokens = []

        # Add native token
        tokens.append({
            'address': self.node.get_native_token_address(),
            'type': 'native',
            'symbol': 'ETH'
        })

        # Add ERC20 tokens
        for addr in self.node.token_manager.supported_tokens:
            tokens.append({
                'address': addr,
                'type': 'erc20'
            })

        return aiohttp.web.json_response({'tokens': tokens})

    async def _handle_add_token(self, request):
        """Add a new supported token."""
        try:
            data = await request.json()
        except Exception:
            raise ValidationError("Invalid JSON body")

        address = validate_eth_address(data.get('address'), 'address')
        abi = data.get('abi')

        if not abi or not isinstance(abi, list):
            raise ValidationError("abi is required and must be an array", 'abi')

        try:
            self.node.token_manager.add_supported_token(address, abi)
            return aiohttp.web.json_response({
                'success': True,
                'address': address
            }, status=201)
        except Exception as e:
            return aiohttp.web.json_response(
                {'error': str(e)},
                status=400
            )

    async def _handle_share_data(self, request):
        """Share encrypted data with a recipient."""
        try:
            data = await request.json()
        except Exception:
            raise ValidationError("Invalid JSON body")

        validated = validate_share_data_request(data)

        try:
            tx_hash = await self.node.share_data(
                validated.data,
                validated.recipient,
                validated.payment_token,
                validated.payment_amount
            )
            return aiohttp.web.json_response({
                'success': True,
                'tx_hash': tx_hash,
                'recipient': validated.recipient
            }, status=201)
        except ValueError as e:
            return aiohttp.web.json_response(
                {'error': str(e)},
                status=400
            )

    async def _handle_get_data(self, request):
        """Retrieve shared data by hash."""
        data_hash = request.match_info['data_hash']
        data_hash = validate_hash(data_hash, 'data_hash')

        try:
            data = await self.node.get_shared_data(data_hash)
            if data is None:
                return aiohttp.web.json_response(
                    {'error': 'Data not found'},
                    status=404
                )
            return aiohttp.web.json_response({
                'hash': data_hash,
                'data': data
            })
        except Exception as e:
            logger.error(f"Error retrieving data {data_hash}: {e}")
            return aiohttp.web.json_response(
                {'error': 'Failed to retrieve data'},
                status=500
            )

    async def _handle_verify_data(self, request):
        """Verify data compliance on blockchain."""
        data_hash = request.match_info['data_hash']
        data_hash = validate_hash(data_hash, 'data_hash')

        try:
            is_verified = self.node.compliance_manager.verify_compliance(
                'data_share',
                data_hash
            )
            return aiohttp.web.json_response({
                'hash': data_hash,
                'verified': is_verified,
                'event_type': 'data_share'
            })
        except Exception as e:
            logger.error(f"Compliance verification failed: {e}")
            return aiohttp.web.json_response(
                {'error': 'Verification failed'},
                status=500
            )

    async def _handle_compliance_history(self, request):
        """Get compliance event history."""
        filters_str = request.query.get('filters')
        filters = validate_filters(filters_str)

        try:
            history = self.node.compliance_manager.get_compliance_history(filters)
            return aiohttp.web.json_response({
                'history': history,
                'count': len(history),
                'filters': filters
            })
        except Exception as e:
            logger.error(f"Failed to get compliance history: {e}")
            return aiohttp.web.json_response(
                {'error': 'Failed to retrieve history'},
                status=500
            )

    async def _handle_network_stats(self, request):
        """Get P2P network statistics."""
        stats = self.node.p2p_network.get_network_stats()
        return aiohttp.web.json_response(stats)

    async def _handle_network_peers(self, request):
        """Get list of connected peers."""
        healthy_only = request.query.get('healthy', 'false').lower() == 'true'

        if healthy_only:
            peers = self.node.p2p_network.get_healthy_peers()
        else:
            peers = self.node.p2p_network.get_connected_peers()

        return aiohttp.web.json_response({
            'peers': peers,
            'count': len(peers)
        })

    async def _handle_dashboard_info(self, request):
        """Get dashboard-specific information."""
        return aiohttp.web.json_response({
            'node_id': self.node.config.node_id,
            'websocket_clients': self.ws_manager.connection_count,
            'event_history_size': self.event_bus.history_size,
            'api_version': '1.0.0',
            'ports': {
                'internal_api': 8080,
                'external_api': 8081,
                'dashboard': self.port
            }
        })
