"""Event bus for dashboard real-time updates."""

import asyncio
import json
import logging
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Set

logger = logging.getLogger(__name__)


class EventType(Enum):
    """Event types for dashboard updates."""

    # Health events
    HEALTH_UPDATE = "health.update"
    COMPONENT_STATUS_CHANGE = "health.component_change"

    # Token events
    BALANCE_UPDATE = "token.balance_update"
    TRANSFER_COMPLETED = "token.transfer_completed"
    TRANSFER_FAILED = "token.transfer_failed"
    TOKEN_ADDED = "token.added"

    # Data events
    DATA_SHARED = "data.shared"
    DATA_RECEIVED = "data.received"
    DATA_VERIFIED = "data.verified"

    # Compliance events
    COMPLIANCE_EVENT = "compliance.event"

    # Network events
    PEER_CONNECTED = "network.peer_connected"
    PEER_DISCONNECTED = "network.peer_disconnected"
    PEER_HEALTH_UPDATE = "network.peer_health"
    NETWORK_STATS_UPDATE = "network.stats_update"

    # System events
    NODE_STARTED = "system.node_started"
    NODE_STOPPING = "system.node_stopping"
    ERROR = "system.error"


@dataclass
class Event:
    """Event data structure for dashboard updates."""

    type: EventType
    data: Dict[str, Any]
    timestamp: float = field(default_factory=time.time)

    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary."""
        return {
            'type': self.type.value,
            'data': self.data,
            'timestamp': self.timestamp
        }

    def to_json(self) -> str:
        """Convert event to JSON string."""
        return json.dumps(self.to_dict())

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Event':
        """Create event from dictionary."""
        return cls(
            type=EventType(data['type']),
            data=data['data'],
            timestamp=data.get('timestamp', time.time())
        )


class EventBus:
    """Central event bus for dashboard updates.

    Provides pub/sub functionality for real-time updates to TUI and web dashboard.
    """

    def __init__(self, max_history: int = 100):
        """Initialize event bus.

        Args:
            max_history: Maximum number of events to keep in history.
        """
        self._subscribers: Dict[EventType, Set[Callable]] = {}
        self._global_subscribers: Set[Callable] = set()
        self._event_history: List[Event] = []
        self._max_history = max_history
        self._lock = asyncio.Lock()

    def subscribe(self, event_type: EventType, callback: Callable) -> None:
        """Subscribe to a specific event type.

        Args:
            event_type: The event type to subscribe to.
            callback: Callback function to call when event occurs.
                     Can be sync or async.
        """
        if event_type not in self._subscribers:
            self._subscribers[event_type] = set()
        self._subscribers[event_type].add(callback)
        logger.debug(f"Subscribed to {event_type.value}")

    def subscribe_all(self, callback: Callable) -> None:
        """Subscribe to all events.

        Useful for WebSocket broadcast.

        Args:
            callback: Callback function to call for all events.
        """
        self._global_subscribers.add(callback)
        logger.debug("Subscribed to all events")

    def unsubscribe(self, event_type: EventType, callback: Callable) -> None:
        """Unsubscribe from a specific event type.

        Args:
            event_type: The event type to unsubscribe from.
            callback: The callback to remove.
        """
        if event_type in self._subscribers:
            self._subscribers[event_type].discard(callback)
            logger.debug(f"Unsubscribed from {event_type.value}")

    def unsubscribe_all(self, callback: Callable) -> None:
        """Unsubscribe from all events.

        Args:
            callback: The callback to remove from global subscribers.
        """
        self._global_subscribers.discard(callback)
        logger.debug("Unsubscribed from all events")

    async def publish(self, event: Event) -> None:
        """Publish an event to all subscribers.

        Args:
            event: The event to publish.
        """
        async with self._lock:
            # Store in history
            self._event_history.append(event)
            if len(self._event_history) > self._max_history:
                self._event_history.pop(0)

        # Notify type-specific subscribers
        if event.type in self._subscribers:
            for callback in list(self._subscribers[event.type]):
                await self._invoke_callback(callback, event)

        # Notify global subscribers
        for callback in list(self._global_subscribers):
            await self._invoke_callback(callback, event)

        logger.debug(f"Published event: {event.type.value}")

    async def _invoke_callback(self, callback: Callable, event: Event) -> None:
        """Invoke a callback, handling both sync and async callbacks.

        Args:
            callback: The callback to invoke.
            event: The event to pass to the callback.
        """
        try:
            if asyncio.iscoroutinefunction(callback):
                await callback(event)
            else:
                callback(event)
        except Exception as e:
            logger.error(f"Event callback error: {e}")

    def get_recent_events(self, count: int = 50) -> List[Event]:
        """Get recent events from history.

        Useful for sending to new WebSocket connections.

        Args:
            count: Maximum number of events to return.

        Returns:
            List of recent events.
        """
        return self._event_history[-count:]

    def get_events_by_type(
        self,
        event_type: EventType,
        count: int = 50
    ) -> List[Event]:
        """Get recent events of a specific type.

        Args:
            event_type: The event type to filter by.
            count: Maximum number of events to return.

        Returns:
            List of matching events.
        """
        matching = [e for e in self._event_history if e.type == event_type]
        return matching[-count:]

    def clear_history(self) -> None:
        """Clear event history."""
        self._event_history.clear()
        logger.debug("Event history cleared")

    @property
    def subscriber_count(self) -> int:
        """Get total number of subscribers."""
        type_subs = sum(len(subs) for subs in self._subscribers.values())
        return type_subs + len(self._global_subscribers)

    @property
    def history_size(self) -> int:
        """Get current size of event history."""
        return len(self._event_history)
