"""HTTP and WebSocket client for TUI dashboard."""

import asyncio
import json
import logging
from typing import Any, Callable, Dict, List, Optional

import aiohttp

logger = logging.getLogger(__name__)


class DashboardClient:
    """HTTP and WebSocket client for TUI communication with Dashboard API.

    Provides methods to fetch data from the Dashboard API and receive
    real-time updates via WebSocket.
    """

    def __init__(self, base_url: str = "http://localhost:8082"):
        """Initialize the dashboard client.

        Args:
            base_url: Base URL of the Dashboard API.
        """
        self.base_url = base_url.rstrip('/')
        self.ws_url = base_url.replace('http', 'ws').rstrip('/') + '/ws'
        self.session: Optional[aiohttp.ClientSession] = None
        self.ws: Optional[aiohttp.ClientWebSocketResponse] = None
        self.on_event: Optional[Callable[[Dict[str, Any]], None]] = None
        self._ws_task: Optional[asyncio.Task] = None
        self._reconnect_delay = 3
        self._should_reconnect = True

    async def _ensure_session(self) -> None:
        """Ensure HTTP session is available."""
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession()

    async def get(self, path: str) -> Optional[Dict[str, Any]]:
        """Make a GET request to the API.

        Args:
            path: API path (e.g., '/api/health').

        Returns:
            Response JSON or None on error.
        """
        await self._ensure_session()
        try:
            async with self.session.get(f"{self.base_url}{path}") as resp:
                if resp.status == 200:
                    return await resp.json()
                logger.warning(f"GET {path} returned {resp.status}")
        except aiohttp.ClientError as e:
            logger.error(f"GET {path} failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in GET {path}: {e}")
        return None

    async def post(
        self,
        path: str,
        data: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Make a POST request to the API.

        Args:
            path: API path (e.g., '/api/transfer').
            data: Request body as dictionary.

        Returns:
            Response JSON or None on error.
        """
        await self._ensure_session()
        try:
            async with self.session.post(
                f"{self.base_url}{path}",
                json=data
            ) as resp:
                return await resp.json()
        except aiohttp.ClientError as e:
            logger.error(f"POST {path} failed: {e}")
        except Exception as e:
            logger.error(f"Unexpected error in POST {path}: {e}")
        return None

    async def connect_websocket(self) -> bool:
        """Connect to WebSocket for real-time updates.

        Returns:
            True if connected successfully.
        """
        await self._ensure_session()
        self._should_reconnect = True

        try:
            self.ws = await self.session.ws_connect(
                self.ws_url,
                heartbeat=30
            )
            self._ws_task = asyncio.create_task(self._ws_loop())
            logger.info("WebSocket connected")
            return True
        except Exception as e:
            logger.error(f"WebSocket connection failed: {e}")
            return False

    async def _ws_loop(self) -> None:
        """WebSocket message loop."""
        try:
            async for msg in self.ws:
                if msg.type == aiohttp.WSMsgType.TEXT:
                    try:
                        event = json.loads(msg.data)
                        if self.on_event:
                            if asyncio.iscoroutinefunction(self.on_event):
                                await self.on_event(event)
                            else:
                                self.on_event(event)
                    except json.JSONDecodeError:
                        logger.warning(f"Invalid WebSocket message: {msg.data[:100]}")
                elif msg.type == aiohttp.WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {self.ws.exception()}")
                    break
                elif msg.type == aiohttp.WSMsgType.CLOSED:
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket loop error: {e}")

        # Attempt reconnection
        if self._should_reconnect:
            logger.info(f"Reconnecting in {self._reconnect_delay}s...")
            await asyncio.sleep(self._reconnect_delay)
            await self.connect_websocket()

    async def disconnect(self) -> None:
        """Disconnect from WebSocket and close session."""
        self._should_reconnect = False

        if self._ws_task:
            self._ws_task.cancel()
            try:
                await self._ws_task
            except asyncio.CancelledError:
                pass
            self._ws_task = None

        if self.ws and not self.ws.closed:
            await self.ws.close()
            self.ws = None

        if self.session and not self.session.closed:
            await self.session.close()
            self.session = None

        logger.info("Dashboard client disconnected")

    async def send_ping(self) -> bool:
        """Send ping to WebSocket.

        Returns:
            True if ping was sent successfully.
        """
        if self.ws and not self.ws.closed:
            try:
                await self.ws.send_json({'type': 'ping'})
                return True
            except Exception as e:
                logger.error(f"Failed to send ping: {e}")
        return False

    # Convenience methods for specific API calls

    async def get_health(self) -> Optional[Dict[str, Any]]:
        """Get node health status."""
        return await self.get('/api/health')

    async def get_balance(self, address: str) -> Optional[Dict[str, Any]]:
        """Get token balance for an address."""
        return await self.get(f'/api/balance/{address}')

    async def get_tokens(self) -> Optional[List[Dict[str, Any]]]:
        """Get list of supported tokens."""
        result = await self.get('/api/tokens')
        return result.get('tokens', []) if result else None

    async def transfer(
        self,
        from_address: str,
        to_address: str,
        amount: int,
        token: str
    ) -> Optional[Dict[str, Any]]:
        """Transfer tokens between addresses."""
        return await self.post('/api/transfer', {
            'from': from_address,
            'to': to_address,
            'amount': amount,
            'token': token
        })

    async def share_data(
        self,
        data: str,
        recipient: str,
        payment_token: Optional[str] = None,
        payment_amount: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """Share data with a recipient."""
        payload = {
            'data': data,
            'recipient': recipient
        }
        if payment_token:
            payload['payment_token'] = payment_token
            payload['payment_amount'] = payment_amount
        return await self.post('/api/share_data', payload)

    async def get_data(self, data_hash: str) -> Optional[Dict[str, Any]]:
        """Get shared data by hash."""
        return await self.get(f'/api/data/{data_hash}')

    async def verify_data(self, data_hash: str) -> Optional[Dict[str, Any]]:
        """Verify data compliance."""
        return await self.get(f'/api/verify_data/{data_hash}')

    async def get_compliance_history(
        self,
        filters: Optional[List[str]] = None
    ) -> Optional[Dict[str, Any]]:
        """Get compliance event history."""
        path = '/api/compliance_history'
        if filters:
            path += f'?filters={",".join(filters)}'
        return await self.get(path)

    async def get_network_stats(self) -> Optional[Dict[str, Any]]:
        """Get P2P network statistics."""
        return await self.get('/api/network/stats')

    async def get_peers(
        self,
        healthy_only: bool = False
    ) -> Optional[Dict[str, Any]]:
        """Get list of connected peers."""
        path = '/api/network/peers'
        if healthy_only:
            path += '?healthy=true'
        return await self.get(path)

    async def get_dashboard_info(self) -> Optional[Dict[str, Any]]:
        """Get dashboard-specific information."""
        return await self.get('/api/dashboard/info')

    @property
    def is_connected(self) -> bool:
        """Check if WebSocket is connected."""
        return self.ws is not None and not self.ws.closed
