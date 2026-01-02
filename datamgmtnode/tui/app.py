"""Main Textual application for DataMgmt Node TUI."""

import asyncio
from typing import Any, Dict

from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.widgets import Footer, Header

from datamgmtnode.tui.api_client import DashboardClient
from datamgmtnode.tui.screens import (
    ComplianceScreen,
    DataScreen,
    HealthScreen,
    MainScreen,
    NetworkScreen,
    TokensScreen,
    TransfersScreen,
)


class DataMgmtTUI(App):
    """DataMgmt Node Terminal User Interface.

    A comprehensive TUI for monitoring and managing the DataMgmt Node.
    """

    TITLE = "DataMgmt Node"
    SUB_TITLE = "Terminal Dashboard"
    CSS_PATH = "styles/app.tcss"

    BINDINGS = [
        Binding("m", "switch_mode('main')", "Main", show=True),
        Binding("h", "switch_mode('health')", "Health", show=True),
        Binding("t", "switch_mode('tokens')", "Tokens", show=True),
        Binding("x", "switch_mode('transfers')", "Transfers", show=True),
        Binding("d", "switch_mode('data')", "Data", show=True),
        Binding("c", "switch_mode('compliance')", "Compliance", show=True),
        Binding("n", "switch_mode('network')", "Network", show=True),
        Binding("r", "refresh", "Refresh", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    MODES = {
        "main": MainScreen,
        "health": HealthScreen,
        "tokens": TokensScreen,
        "transfers": TransfersScreen,
        "data": DataScreen,
        "compliance": ComplianceScreen,
        "network": NetworkScreen,
    }

    def __init__(self, api_url: str = "http://localhost:8082"):
        """Initialize the TUI application.

        Args:
            api_url: URL of the Dashboard API.
        """
        super().__init__()
        self.client = DashboardClient(api_url)
        self._current_mode = "main"

    def compose(self) -> ComposeResult:
        """Compose the main application layout."""
        yield Header(show_clock=True)
        yield Footer()

    async def on_mount(self) -> None:
        """Handle application mount."""
        # Set up event handler for WebSocket events
        self.client.on_event = self._handle_event

        # Connect to WebSocket
        connected = await self.client.connect_websocket()
        if not connected:
            self.notify(
                "Failed to connect to Dashboard API. Is the node running?",
                severity="warning",
                timeout=5
            )

        # Install and switch to main screen
        for mode_name, screen_class in self.MODES.items():
            self.install_screen(screen_class(self.client), name=mode_name)

        await self.switch_mode("main")

    async def on_unmount(self) -> None:
        """Handle application unmount."""
        await self.client.disconnect()

    def action_switch_mode(self, mode: str) -> None:
        """Switch to a different screen mode.

        Args:
            mode: The mode/screen to switch to.
        """
        if mode in self.MODES and mode != self._current_mode:
            self._current_mode = mode
            self.switch_screen(mode)

    async def switch_mode(self, mode: str) -> None:
        """Async version of mode switching.

        Args:
            mode: The mode/screen to switch to.
        """
        if mode in self.MODES:
            self._current_mode = mode
            await self.switch_screen(mode)

    def action_refresh(self) -> None:
        """Refresh the current screen."""
        screen = self.screen
        if hasattr(screen, 'refresh_data'):
            asyncio.create_task(screen.refresh_data())

    async def _handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events.

        Args:
            event: The event data from WebSocket.
        """
        event_type = event.get('type', '')

        # Update notification for important events
        if event_type == 'system.error':
            self.notify(
                f"Error: {event.get('data', {}).get('message', 'Unknown error')}",
                severity="error",
                timeout=5
            )
        elif event_type == 'token.transfer_completed':
            self.notify(
                "Transfer completed successfully",
                severity="information",
                timeout=3
            )
        elif event_type == 'data.shared':
            self.notify(
                "Data shared successfully",
                severity="information",
                timeout=3
            )

        # Forward event to current screen
        screen = self.screen
        if hasattr(screen, 'handle_event'):
            await screen.handle_event(event)


def run_tui(api_url: str = "http://localhost:8082") -> None:
    """Run the TUI application.

    Args:
        api_url: URL of the Dashboard API.
    """
    app = DataMgmtTUI(api_url=api_url)
    app.run()


if __name__ == "__main__":
    run_tui()
