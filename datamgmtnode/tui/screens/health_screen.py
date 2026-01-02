"""Health status screen for TUI."""

from typing import Any, Dict

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.reactive import reactive
from textual.screen import Screen
from textual.widgets import Label, Static

from datamgmtnode.tui.api_client import DashboardClient


class HealthScreen(Screen):
    """Health status screen showing component details."""

    BINDINGS = [("r", "refresh", "Refresh")]

    status = reactive("unknown")
    blockchain_status = reactive("unknown")
    p2p_status = reactive("unknown")
    encryption_status = reactive("unknown")

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Health Status", id="screen-title"),
            Vertical(
                Container(
                    Label("Overall Status", classes="component-label"),
                    Static("...", id="overall-status", classes="status-value"),
                    classes="status-row"
                ),
                Container(
                    Label("Version", classes="component-label"),
                    Static("...", id="version", classes="status-value"),
                    classes="status-row"
                ),
                Container(
                    Label("Node ID", classes="component-label"),
                    Static("...", id="node-id", classes="status-value"),
                    classes="status-row"
                ),
                id="overview-section"
            ),
            Vertical(
                Label("Components", classes="section-title"),
                Container(
                    Label("Blockchain", classes="component-label"),
                    Static("...", id="blockchain-status", classes="status-value"),
                    classes="status-row"
                ),
                Container(
                    Label("P2P Network", classes="component-label"),
                    Static("...", id="p2p-status", classes="status-value"),
                    classes="status-row"
                ),
                Container(
                    Label("Encryption", classes="component-label"),
                    Static("...", id="encryption-status", classes="status-value"),
                    classes="status-row"
                ),
                id="components-section"
            ),
            id="health-container"
        )

    async def on_mount(self) -> None:
        """Handle screen mount."""
        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh health data."""
        health = await self.client.get_health()
        if health:
            # Overall status
            status = health.get('status', 'unknown')
            self.status = status
            status_widget = self.query_one("#overall-status", Static)
            if status == 'healthy':
                status_widget.update("[green]Healthy[/]")
            elif status == 'degraded':
                status_widget.update("[yellow]Degraded[/]")
            else:
                status_widget.update("[red]Unhealthy[/]")

            # Version and Node ID
            self.query_one("#version", Static).update(
                health.get('version', 'unknown')
            )
            self.query_one("#node-id", Static).update(
                health.get('node_id', 'unknown')
            )

            # Components
            components = health.get('components', {})

            blockchain = components.get('blockchain', 'unknown')
            self.blockchain_status = blockchain
            bc_widget = self.query_one("#blockchain-status", Static)
            if blockchain == 'connected':
                bc_widget.update("[green]Connected[/]")
            else:
                bc_widget.update(f"[red]{blockchain.capitalize()}[/]")

            p2p = components.get('p2p_network', 'unknown')
            self.p2p_status = p2p
            p2p_widget = self.query_one("#p2p-status", Static)
            if p2p == 'running':
                p2p_widget.update("[green]Running[/]")
            else:
                p2p_widget.update(f"[red]{p2p.capitalize()}[/]")

            encryption = components.get('encryption', 'unknown')
            self.encryption_status = encryption
            enc_widget = self.query_one("#encryption-status", Static)
            if encryption == 'initialized':
                enc_widget.update("[green]Initialized[/]")
            else:
                enc_widget.update(f"[yellow]{encryption.capitalize()}[/]")

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')
        if event_type == 'health.update':
            await self.refresh_data()

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.app.run_worker(self.refresh_data())
