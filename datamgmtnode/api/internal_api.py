import logging
import aiohttp.web
from api.validation import (
    ValidationError,
    validate_transfer_request,
    validate_eth_address
)
from api.rate_limiter import create_internal_rate_limiter, create_rate_limit_middleware

logger = logging.getLogger(__name__)


class InternalAPI:
    """Internal API for node management operations (port 8080)."""

    def __init__(self, node):
        self.node = node
        self.runner = None
        self.rate_limiter = create_internal_rate_limiter()

    async def start(self):
        rate_limit_middleware = create_rate_limit_middleware(self.rate_limiter)
        app = aiohttp.web.Application(middlewares=[rate_limit_middleware, self.error_middleware])
        app.router.add_get('/health', self.health_check)
        app.router.add_get('/balance/{address}', self.get_balance)
        app.router.add_post('/transfer', self.transfer)
        app.router.add_get('/tokens', self.list_tokens)
        app.router.add_post('/tokens', self.add_token)

        self.runner = aiohttp.web.AppRunner(app)
        await self.runner.setup()
        site = aiohttp.web.TCPSite(self.runner, 'localhost', 8080)
        await site.start()
        logger.info("Internal API started on port 8080")

    async def stop(self):
        if self.runner:
            await self.runner.cleanup()
            logger.info("Internal API stopped")

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
            logger.exception(f"Internal error: {e}")
            return aiohttp.web.json_response(
                {'error': 'Internal server error'},
                status=500
            )

    async def health_check(self, request):
        """Health check endpoint."""
        try:
            # Check critical components
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
                'version': '0.1.0'
            })
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return aiohttp.web.json_response(
                {'status': 'unhealthy', 'error': str(e)},
                status=503
            )

    async def get_balance(self, request):
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

    async def transfer(self, request):
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

    async def list_tokens(self, request):
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

    async def add_token(self, request):
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
