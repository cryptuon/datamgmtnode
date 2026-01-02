"""Main dashboard screen for TUI."""

from typing import Any, Dict

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Label, Static

from datamgmtnode.tui.api_client import DashboardClient


class StatCard(Static):
    """A card widget displaying a statistic."""

    def __init__(
        self,
        title: str,
        value: str = "...",
        variant: str = "default",
        **kwargs
    ):
        super().__init__(**kwargs)
        self.title = title
        self._value = value
        self.variant = variant

    def compose(self) -> ComposeResult:
        yield Label(self.title, classes="stat-title")
        yield Label(self._value, classes="stat-value")

    def update_value(self, value: str, variant: str = None) -> None:
        """Update the displayed value."""
        self._value = value
        value_label = self.query_one(".stat-value", Label)
        value_label.update(value)
        if variant:
            self.variant = variant
            self.remove_class("success", "warning", "error", "default")
            self.add_class(variant)


class MainScreen(Screen):
    """Main dashboard overview screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    status = reactive("...")
    peer_count = reactive(0)
    healthy_peers = reactive(0)
    ws_clients = reactive(0)

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield Container(
            Label("DataMgmt Node Dashboard", id="screen-title"),
            Horizontal(
                StatCard("Node Status", id="stat-status", classes="stat-card"),
                StatCard("Total Peers", id="stat-peers", classes="stat-card"),
                StatCard("Healthy Peers", id="stat-healthy", classes="stat-card"),
                StatCard("WS Clients", id="stat-ws", classes="stat-card"),
                id="stats-row"
            ),
            Vertical(
                Label("Components", classes="section-title"),
                Container(
                    Static("Blockchain: ...", id="comp-blockchain"),
                    Static("P2P Network: ...", id="comp-p2p"),
                    Static("Encryption: ...", id="comp-encryption"),
                    id="components-grid"
                ),
                id="components-section"
            ),
            Vertical(
                Label("Recent Events", classes="section-title"),
                Container(id="events-list"),
                id="events-section"
            ),
            id="main-container"
        )

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh all dashboard data."""
        # Fetch health
        health = await self.client.get_health()
        if health:
            status = health.get('status', 'unknown')
            self.status = status

            status_card = self.query_one("#stat-status", StatCard)
            variant = "success" if status == "healthy" else "warning"
            status_card.update_value(status.capitalize(), variant)

            # Update components
            components = health.get('components', {})
            self.query_one("#comp-blockchain").update(
                f"Blockchain: {components.get('blockchain', 'unknown')}"
            )
            self.query_one("#comp-p2p").update(
                f"P2P Network: {components.get('p2p_network', 'unknown')}"
            )
            self.query_one("#comp-encryption").update(
                f"Encryption: {components.get('encryption', 'unknown')}"
            )

        # Fetch network stats
        stats = await self.client.get_network_stats()
        if stats:
            self.peer_count = stats.get('total_peers', 0)
            self.healthy_peers = stats.get('healthy_peers', 0)

            self.query_one("#stat-peers", StatCard).update_value(
                str(self.peer_count)
            )
            self.query_one("#stat-healthy", StatCard).update_value(
                str(self.healthy_peers), "success"
            )

        # Fetch dashboard info
        info = await self.client.get_dashboard_info()
        if info:
            self.ws_clients = info.get('websocket_clients', 0)
            self.query_one("#stat-ws", StatCard).update_value(
                str(self.ws_clients)
            )

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')

        if event_type in ('health.update', 'network.stats_update'):
            await self.refresh_data()

        # Add to recent events list
        events_list = self.query_one("#events-list", Container)
        timestamp = event.get('timestamp', 0)
        from datetime import datetime
        time_str = datetime.fromtimestamp(timestamp).strftime('%H:%M:%S')

        event_widget = Static(
            f"[dim]{time_str}[/] {event_type}",
            classes="event-item"
        )
        events_list.mount(event_widget)

        # Keep only last 10 events
        children = list(events_list.children)
        if len(children) > 10:
            children[0].remove()

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.app.run_worker(self.refresh_data())
