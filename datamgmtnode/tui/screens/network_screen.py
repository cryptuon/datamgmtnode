"""Network and peers screen for TUI."""

from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Checkbox, DataTable, Label, Static

from datamgmtnode.tui.api_client import DashboardClient


class NetworkScreen(Screen):
    """Network statistics and peer management screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    total_peers = reactive(0)
    healthy_peers = reactive(0)
    avg_latency = reactive(0.0)

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.peers: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Network", id="screen-title"),
            Horizontal(
                Container(
                    Label("Total Peers", classes="stat-label"),
                    Static("0", id="total-peers-value", classes="stat-value"),
                    classes="stat-card"
                ),
                Container(
                    Label("Healthy Peers", classes="stat-label"),
                    Static("0", id="healthy-peers-value", classes="stat-value success"),
                    classes="stat-card"
                ),
                Container(
                    Label("Avg Latency", classes="stat-label"),
                    Static("0 ms", id="avg-latency-value", classes="stat-value"),
                    classes="stat-card"
                ),
                id="stats-row"
            ),
            Vertical(
                Horizontal(
                    Label("Connected Peers", classes="section-title"),
                    Checkbox("Healthy only", id="healthy-only-checkbox"),
                    id="peers-header"
                ),
                DataTable(id="peers-table"),
                id="peers-section"
            ),
            id="network-container"
        )

    async def on_mount(self) -> None:
        """Handle screen mount."""
        table = self.query_one("#peers-table", DataTable)
        table.add_columns(
            "Host", "Port", "Node ID", "Latency (ms)", "Status", "Success Rate"
        )
        table.cursor_type = "row"

        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh network data."""
        # Fetch network stats
        stats = await self.client.get_network_stats()
        if stats:
            self.total_peers = stats.get('total_peers', 0)
            self.healthy_peers = stats.get('healthy_peers', 0)
            self.avg_latency = stats.get('avg_latency_ms', 0.0)

            self.query_one("#total-peers-value", Static).update(
                str(self.total_peers)
            )
            self.query_one("#healthy-peers-value", Static).update(
                str(self.healthy_peers)
            )
            self.query_one("#avg-latency-value", Static).update(
                f"{self.avg_latency:.1f} ms"
            )

        # Fetch peers
        checkbox = self.query_one("#healthy-only-checkbox", Checkbox)
        healthy_only = checkbox.value

        peers_result = await self.client.get_peers(healthy_only=healthy_only)
        if peers_result:
            self.peers = peers_result.get('peers', [])
            await self._update_peers_table()

    async def _update_peers_table(self) -> None:
        """Update the peers table with current data."""
        table = self.query_one("#peers-table", DataTable)
        table.clear()

        for peer in self.peers:
            host = peer.get('host', 'N/A')
            port = str(peer.get('port', 'N/A'))

            node_id = peer.get('node_id', 'N/A')
            display_id = f"{node_id[:12]}..." if node_id and len(node_id) > 12 else node_id

            latency = peer.get('latency_ms', 0)
            latency_str = f"{latency:.1f}"

            is_healthy = peer.get('healthy', False)
            status = "[green]Healthy[/]" if is_healthy else "[red]Unhealthy[/]"

            success_rate = peer.get('success_rate', 0)
            rate_str = f"{success_rate * 100:.1f}%"

            table.add_row(host, port, display_id, latency_str, status, rate_str)

    async def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        """Handle checkbox state changes."""
        if event.checkbox.id == "healthy-only-checkbox":
            await self.refresh_data()

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')

        if event_type.startswith('network.'):
            await self.refresh_data()

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.app.run_worker(self.refresh_data())
