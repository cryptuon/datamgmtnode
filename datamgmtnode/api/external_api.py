import logging
import aiohttp.web
from api.validation import (
    ValidationError,
    validate_share_data_request,
    validate_hash,
    validate_filters,
    validate_eth_address
)
from api.rate_limiter import create_external_rate_limiter, create_rate_limit_middleware

logger = logging.getLogger(__name__)


class ExternalAPI:
    """External API for data sharing operations (port 8081)."""

    def __init__(self, node):
        self.node = node
        self.runner = None
        self.rate_limiter = create_external_rate_limiter()

    async def start(self):
        rate_limit_middleware = create_rate_limit_middleware(self.rate_limiter)
        app = aiohttp.web.Application(middlewares=[rate_limit_middleware, self.error_middleware])
        app.router.add_get('/health', self.health_check)
        app.router.add_post('/share_data', self.share_data)
        app.router.add_get('/data/{data_hash}', self.get_data)
        app.router.add_get('/verify_data/{data_hash}', self.verify_data)
        app.router.add_get('/compliance_history', self.get_compliance_history)
        app.router.add_get('/network/stats', self.get_network_stats)
        app.router.add_get('/network/peers', self.get_peers)

        self.runner = aiohttp.web.AppRunner(app)
        await self.runner.setup()
        site = aiohttp.web.TCPSite(self.runner, '0.0.0.0', 8081)
        await site.start()
        logger.info("External API started on port 8081")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
            logger.info("External API stopped")

    @aiohttp.web.middleware
    async def error_middleware(self, request, handler):
        """Global error handling middleware."""
        try:
            return await handler(request)
        except ValidationError as e:
            logger.warning(f"Validation error: {e.message} (field: {e.field})")
            return aiohttp.web.json_response(
                {'error': e.message, 'field': e.field},
                status=422
            )
        except aiohttp.web.HTTPException:
            raise
        except Exception as e:
            logger.exception(f"External API error: {e}")
            return aiohttp.web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    async def health_check(self, request):
        """Health check endpoint."""
        p2p_stats = self.node.p2p_network.get_network_stats()
        return aiohttp.web.json_response({
            'status': 'healthy' if self.node.p2p_network.is_running else 'degraded',
            'p2p': {
                'running': self.node.p2p_network.is_running,
                'peers': p2p_stats['healthy_peers']
            }
        })

    async def share_data(self, request):
        """Share encrypted data with a recipient."""
        # Parse and validate request
        try:
            data = await request.json()
        except Exception:
            raise ValidationError("Invalid JSON body")

        validated = validate_share_data_request(data)

        # Access control: verify the sender is authorized
        # For now, check if the node signature authorizes this operation
        # In production, this should verify API keys or JWT tokens
        api_key = request.headers.get('X-API-Key')
        if not self._verify_api_access(api_key):
            logger.warning(f"Unauthorized share_data attempt")
            return aiohttp.web.json_response(
                {'error': 'Unauthorized. Provide valid X-API-Key header.'},
                status=401
            )

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

    async def get_data(self, request):
        """Retrieve shared data by hash."""
        data_hash = request.match_info['data_hash']
        data_hash = validate_hash(data_hash, 'data_hash')

        # Access control
        api_key = request.headers.get('X-API-Key')
        if not self._verify_api_access(api_key):
            return aiohttp.web.json_response(
                {'error': 'Unauthorized'},
                status=401
            )

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

    async def verify_data(self, request):
        """Verify data compliance on blockchain."""
        data_hash = request.match_info['data_hash']
        data_hash = validate_hash(data_hash, 'data_hash')

        try:
            is_verified = self.node.compliance_manager.verify_compliance('data_share', data_hash)
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

    async def get_compliance_history(self, request):
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

    async def get_network_stats(self, request):
        """Get P2P network statistics."""
        stats = self.node.p2p_network.get_network_stats()
        return aiohttp.web.json_response(stats)

    async def get_peers(self, request):
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

    def _verify_api_access(self, api_key: str) -> bool:
        """
        Verify API access key.

        In production, this should:
        - Validate against stored API keys
        - Check rate limits
        - Log access attempts
        """
        # For development: allow if API key matches node_id or is set in config
        if not api_key:
            # Allow unauthenticated access in development mode
            # TODO: Make this configurable
            return True

        # Simple validation: check against node_id
        if api_key == self.node.config.node_id:
            return True

        # Check against configured API key
        configured_key = getattr(self.node.config, 'api_key', None)
        if configured_key and api_key == configured_key:
            return True

        return False
