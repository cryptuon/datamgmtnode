"""Transfers screen for TUI."""

from typing import Any, Dict

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static

from datamgmtnode.tui.api_client import DashboardClient


class TransfersScreen(Screen):
    """Token transfers screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Token Transfers", id="screen-title"),
            Vertical(
                Label("Transfer Tokens", classes="section-title"),
                Container(
                    Label("From Address"),
                    Input(placeholder="0x...", id="from-address"),
                    id="from-row"
                ),
                Container(
                    Label("To Address"),
                    Input(placeholder="0x...", id="to-address"),
                    id="to-row"
                ),
                Container(
                    Label("Amount"),
                    Input(placeholder="Amount in wei", id="amount"),
                    id="amount-row"
                ),
                Container(
                    Label("Token Address"),
                    Input(placeholder="0x... (leave empty for native)", id="token-address"),
                    id="token-row"
                ),
                Container(
                    Button("Transfer", id="transfer-btn", variant="primary"),
                    Button("Clear", id="clear-btn", variant="default"),
                    id="button-row"
                ),
                id="form-section"
            ),
            Vertical(
                Label("Result", classes="section-title"),
                Container(id="result-container"),
                id="result-section"
            ),
            Vertical(
                Label("Recent Transfers", classes="section-title"),
                Container(id="transfers-list"),
                id="history-section"
            ),
            id="transfers-container"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "transfer-btn":
            await self._do_transfer()
        elif event.button.id == "clear-btn":
            self._clear_form()

    def _clear_form(self) -> None:
        """Clear the transfer form."""
        self.query_one("#from-address", Input).value = ""
        self.query_one("#to-address", Input).value = ""
        self.query_one("#amount", Input).value = ""
        self.query_one("#token-address", Input).value = ""
        self.query_one("#result-container", Container).remove_children()

    async def _do_transfer(self) -> None:
        """Execute the transfer."""
        from_addr = self.query_one("#from-address", Input).value.strip()
        to_addr = self.query_one("#to-address", Input).value.strip()
        amount_str = self.query_one("#amount", Input).value.strip()
        token = self.query_one("#token-address", Input).value.strip()

        # Validation
        if not from_addr or not to_addr:
            self.app.notify("From and To addresses are required", severity="warning")
            return

        if not from_addr.startswith("0x") or len(from_addr) != 42:
            self.app.notify("Invalid From address format", severity="error")
            return

        if not to_addr.startswith("0x") or len(to_addr) != 42:
            self.app.notify("Invalid To address format", severity="error")
            return

        try:
            amount = int(amount_str)
            if amount <= 0:
                raise ValueError()
        except ValueError:
            self.app.notify("Amount must be a positive integer", severity="error")
            return

        if not token:
            # Use native token (need to fetch from API)
            tokens = await self.client.get_tokens()
            if tokens:
                native = next((t for t in tokens if t.get('type') == 'native'), None)
                if native:
                    token = native.get('address', '')

        if not token:
            self.app.notify("Token address required", severity="error")
            return

        # Execute transfer
        result_container = self.query_one("#result-container", Container)
        result_container.remove_children()
        result_container.mount(Static("[yellow]Processing transfer...[/]"))

        result = await self.client.transfer(from_addr, to_addr, amount, token)

        result_container.remove_children()
        if result:
            if result.get('success'):
                tx_hash = result.get('tx_hash', 'unknown')
                result_container.mount(
                    Static(f"[green]Transfer successful![/]\nTx: {tx_hash[:20]}...")
                )
                self._add_to_history(from_addr, to_addr, amount, True)
            else:
                error = result.get('error', 'Unknown error')
                result_container.mount(
                    Static(f"[red]Transfer failed: {error}[/]")
                )
                self._add_to_history(from_addr, to_addr, amount, False)
        else:
            result_container.mount(
                Static("[red]Failed to execute transfer[/]")
            )

    def _add_to_history(
        self,
        from_addr: str,
        to_addr: str,
        amount: int,
        success: bool
    ) -> None:
        """Add transfer to history list."""
        history = self.query_one("#transfers-list", Container)

        status = "[green]OK[/]" if success else "[red]FAIL[/]"
        entry = Static(
            f"{status} {from_addr[:8]}... -> {to_addr[:8]}... ({amount})",
            classes="history-item"
        )
        history.mount(entry, before=0)

        # Keep only last 5
        children = list(history.children)
        if len(children) > 5:
            children[-1].remove()

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')
        if event_type == 'token.transfer_completed':
            data = event.get('data', {})
            self._add_to_history(
                data.get('from', ''),
                data.get('to', ''),
                int(data.get('amount', 0)),
                True
            )
        elif event_type == 'token.transfer_failed':
            data = event.get('data', {})
            self._add_to_history(
                data.get('from', ''),
                data.get('recipient', ''),
                int(data.get('amount', 0)),
                False
            )

    async def refresh_data(self) -> None:
        """Refresh screen data."""
        pass  # No persistent data to refresh

    def action_refresh(self) -> None:
        """Handle refresh action."""
        pass
