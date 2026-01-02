"""WebSocket handler for real-time dashboard updates."""

import asyncio
import json
import logging
from typing import Optional, Set

from aiohttp import WSMsgType, web

from datamgmtnode.dashboard.event_bus import Event, EventBus

logger = logging.getLogger(__name__)


class WebSocketManager:
    """Manages WebSocket connections for real-time updates.

    Handles connection lifecycle, message routing, and event broadcasting
    to all connected TUI and web dashboard clients.
    """

    def __init__(self, event_bus: EventBus):
        """Initialize WebSocket manager.

        Args:
            event_bus: Event bus instance for subscribing to events.
        """
        self.event_bus = event_bus
        self.connections: Set[web.WebSocketResponse] = set()
        self._lock = asyncio.Lock()

        # Subscribe to all events for broadcast
        event_bus.subscribe_all(self._broadcast_event)

    async def handle_websocket(self, request: web.Request) -> web.WebSocketResponse:
        """Handle new WebSocket connection.

        Args:
            request: The incoming HTTP request to upgrade.

        Returns:
            WebSocket response object.
        """
        ws = web.WebSocketResponse(heartbeat=30)
        await ws.prepare(request)

        client_ip = request.remote or 'unknown'

        async with self._lock:
            self.connections.add(ws)

        logger.info(
            f"WebSocket connected from {client_ip}. "
            f"Total connections: {len(self.connections)}"
        )

        # Send initial state to new connection
        await self._send_initial_state(ws)

        try:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    await self._handle_message(ws, msg.data)
                elif msg.type == WSMsgType.ERROR:
                    logger.error(f"WebSocket error: {ws.exception()}")
                    break
        except asyncio.CancelledError:
            pass
        except Exception as e:
            logger.error(f"WebSocket handler error: {e}")
        finally:
            async with self._lock:
                self.connections.discard(ws)
            logger.info(
                f"WebSocket disconnected from {client_ip}. "
                f"Total connections: {len(self.connections)}"
            )

        return ws

    async def _send_initial_state(self, ws: web.WebSocketResponse) -> None:
        """Send current state to new connection.

        Args:
            ws: The WebSocket connection.
        """
        try:
            # Send connection acknowledgment
            await ws.send_json({
                'type': 'connected',
                'data': {
                    'message': 'WebSocket connection established',
                    'history_available': self.event_bus.history_size
                }
            })

            # Send recent events for context
            recent = self.event_bus.get_recent_events(20)
            for event in recent:
                await ws.send_str(event.to_json())

        except Exception as e:
            logger.error(f"Error sending initial state: {e}")

    async def _handle_message(
        self,
        ws: web.WebSocketResponse,
        data: str
    ) -> None:
        """Handle incoming WebSocket message.

        Args:
            ws: The WebSocket connection.
            data: The message data as string.
        """
        try:
            message = json.loads(data)
            msg_type = message.get('type')

            if msg_type == 'ping':
                await ws.send_json({'type': 'pong'})

            elif msg_type == 'get_history':
                # Client requesting event history
                count = message.get('count', 50)
                events = self.event_bus.get_recent_events(count)
                await ws.send_json({
                    'type': 'history',
                    'data': {
                        'events': [e.to_dict() for e in events],
                        'count': len(events)
                    }
                })

            elif msg_type == 'subscribe':
                # Future: Handle subscription to specific event types
                event_types = message.get('data', {}).get('events', [])
                logger.debug(f"Client subscribed to: {event_types}")

            else:
                logger.warning(f"Unknown WebSocket message type: {msg_type}")

        except json.JSONDecodeError:
            logger.warning(f"Invalid WebSocket message: {data[:100]}")
        except Exception as e:
            logger.error(f"Error handling WebSocket message: {e}")

    async def _broadcast_event(self, event: Event) -> None:
        """Broadcast event to all connected clients.

        Args:
            event: The event to broadcast.
        """
        if not self.connections:
            return

        message = event.to_json()
        dead_connections: Set[web.WebSocketResponse] = set()

        async with self._lock:
            for ws in self.connections:
                try:
                    if not ws.closed:
                        await ws.send_str(message)
                except Exception as e:
                    logger.warning(f"Failed to send to WebSocket: {e}")
                    dead_connections.add(ws)

            # Remove dead connections
            self.connections -= dead_connections

        if dead_connections:
            logger.debug(f"Removed {len(dead_connections)} dead connections")

    async def close_all(self) -> None:
        """Close all WebSocket connections gracefully."""
        async with self._lock:
            for ws in list(self.connections):
                try:
                    await ws.close(
                        code=1001,
                        message=b'Server shutting down'
                    )
                except Exception as e:
                    logger.warning(f"Error closing WebSocket: {e}")
            self.connections.clear()

        logger.info("All WebSocket connections closed")

    @property
    def connection_count(self) -> int:
        """Get number of active connections."""
        return len(self.connections)

    async def send_to_all(self, message: dict) -> int:
        """Send a custom message to all connected clients.

        Args:
            message: Dictionary to send as JSON.

        Returns:
            Number of clients message was sent to.
        """
        if not self.connections:
            return 0

        sent_count = 0
        message_str = json.dumps(message)

        async with self._lock:
            for ws in list(self.connections):
                try:
                    if not ws.closed:
                        await ws.send_str(message_str)
                        sent_count += 1
                except Exception:
                    pass

        return sent_count
