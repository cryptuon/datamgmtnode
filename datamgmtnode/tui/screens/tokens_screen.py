"""Tokens screen for TUI."""

from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import DataTable, Input, Label, Button

from datamgmtnode.tui.api_client import DashboardClient


class TokensScreen(Screen):
    """Tokens management screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.tokens: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Tokens", id="screen-title"),
            Vertical(
                Label("Supported Tokens", classes="section-title"),
                DataTable(id="tokens-table"),
                id="tokens-section"
            ),
            Vertical(
                Label("Check Balance", classes="section-title"),
                Container(
                    Input(placeholder="Enter address (0x...)", id="balance-address"),
                    Button("Check", id="check-balance-btn", variant="primary"),
                    id="balance-form"
                ),
                Container(id="balance-result"),
                id="balance-section"
            ),
            id="tokens-container"
        )

    async def on_mount(self) -> None:
        """Handle screen mount."""
        # Set up table
        table = self.query_one("#tokens-table", DataTable)
        table.add_columns("Address", "Type", "Symbol")
        table.cursor_type = "row"

        await self.refresh_data()

    async def refresh_data(self) -> None:
        """Refresh tokens data."""
        tokens = await self.client.get_tokens()
        if tokens:
            self.tokens = tokens
            table = self.query_one("#tokens-table", DataTable)
            table.clear()

            for token in tokens:
                address = token.get('address', 'N/A')
                token_type = token.get('type', 'unknown')
                symbol = token.get('symbol', '-')

                # Truncate address for display
                display_addr = f"{address[:10]}...{address[-8:]}" if len(address) > 20 else address

                table.add_row(display_addr, token_type, symbol)

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "check-balance-btn":
            await self._check_balance()

    async def _check_balance(self) -> None:
        """Check balance for the entered address."""
        address_input = self.query_one("#balance-address", Input)
        address = address_input.value.strip()

        if not address:
            self.app.notify("Please enter an address", severity="warning")
            return

        if not address.startswith("0x") or len(address) != 42:
            self.app.notify("Invalid address format", severity="error")
            return

        result = await self.client.get_balance(address)
        result_container = self.query_one("#balance-result", Container)

        # Clear previous results
        result_container.remove_children()

        if result:
            if 'error' in result:
                result_container.mount(
                    Label(f"[red]Error: {result['error']}[/]")
                )
            else:
                balance = result.get('balance', '0')
                token = result.get('token', 'unknown')
                result_container.mount(
                    Label(f"Balance: [green]{balance}[/] ({token[:10]}...)")
                )
        else:
            result_container.mount(
                Label("[red]Failed to fetch balance[/]")
            )

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')
        if event_type in ('token.added', 'token.balance_update'):
            await self.refresh_data()

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.app.run_worker(self.refresh_data())
