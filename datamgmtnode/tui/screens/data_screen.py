"""Data sharing screen for TUI."""

from typing import Any, Dict

from textual.app import ComposeResult
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.widgets import Button, Input, Label, Static, TextArea

from datamgmtnode.tui.api_client import DashboardClient


class DataScreen(Screen):
    """Data sharing and retrieval screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Data Sharing", id="screen-title"),
            Vertical(
                Label("Share Data", classes="section-title"),
                Container(
                    Label("Recipient Address"),
                    Input(placeholder="0x...", id="recipient"),
                    id="recipient-row"
                ),
                Container(
                    Label("Data"),
                    TextArea(id="share-data", language=None),
                    id="data-row"
                ),
                Container(
                    Button("Share", id="share-btn", variant="primary"),
                    Button("Clear", id="clear-share-btn", variant="default"),
                    id="share-buttons"
                ),
                Container(id="share-result"),
                id="share-section"
            ),
            Vertical(
                Label("Retrieve Data", classes="section-title"),
                Container(
                    Label("Data Hash"),
                    Input(placeholder="64-character hex hash", id="data-hash"),
                    id="hash-row"
                ),
                Container(
                    Button("Retrieve", id="retrieve-btn", variant="primary"),
                    Button("Verify", id="verify-btn", variant="default"),
                    id="retrieve-buttons"
                ),
                Container(id="retrieve-result"),
                id="retrieve-section"
            ),
            id="data-container"
        )

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "share-btn":
            await self._share_data()
        elif event.button.id == "clear-share-btn":
            self._clear_share_form()
        elif event.button.id == "retrieve-btn":
            await self._retrieve_data()
        elif event.button.id == "verify-btn":
            await self._verify_data()

    def _clear_share_form(self) -> None:
        """Clear the share form."""
        self.query_one("#recipient", Input).value = ""
        self.query_one("#share-data", TextArea).clear()
        self.query_one("#share-result", Container).remove_children()

    async def _share_data(self) -> None:
        """Share data with recipient."""
        recipient = self.query_one("#recipient", Input).value.strip()
        data = self.query_one("#share-data", TextArea).text.strip()

        if not recipient:
            self.app.notify("Recipient address is required", severity="warning")
            return

        if not recipient.startswith("0x") or len(recipient) != 42:
            self.app.notify("Invalid recipient address format", severity="error")
            return

        if not data:
            self.app.notify("Data is required", severity="warning")
            return

        result_container = self.query_one("#share-result", Container)
        result_container.remove_children()
        result_container.mount(Static("[yellow]Sharing data...[/]"))

        result = await self.client.share_data(data, recipient)

        result_container.remove_children()
        if result:
            if result.get('success'):
                tx_hash = result.get('tx_hash', 'unknown')
                result_container.mount(
                    Static(f"[green]Data shared successfully![/]\nTx: {tx_hash[:30]}...")
                )
            else:
                error = result.get('error', 'Unknown error')
                result_container.mount(
                    Static(f"[red]Failed: {error}[/]")
                )
        else:
            result_container.mount(
                Static("[red]Failed to share data[/]")
            )

    async def _retrieve_data(self) -> None:
        """Retrieve data by hash."""
        data_hash = self.query_one("#data-hash", Input).value.strip()

        if not data_hash:
            self.app.notify("Data hash is required", severity="warning")
            return

        if len(data_hash) != 64:
            self.app.notify("Hash must be 64 characters", severity="error")
            return

        result_container = self.query_one("#retrieve-result", Container)
        result_container.remove_children()
        result_container.mount(Static("[yellow]Retrieving data...[/]"))

        result = await self.client.get_data(data_hash)

        result_container.remove_children()
        if result:
            if 'error' in result:
                result_container.mount(
                    Static(f"[red]Error: {result['error']}[/]")
                )
            else:
                data = result.get('data', '')
                # Truncate if too long
                display_data = data[:200] + "..." if len(str(data)) > 200 else data
                result_container.mount(
                    Static(f"[green]Data found:[/]\n{display_data}")
                )
        else:
            result_container.mount(
                Static("[red]Failed to retrieve data[/]")
            )

    async def _verify_data(self) -> None:
        """Verify data compliance."""
        data_hash = self.query_one("#data-hash", Input).value.strip()

        if not data_hash:
            self.app.notify("Data hash is required", severity="warning")
            return

        if len(data_hash) != 64:
            self.app.notify("Hash must be 64 characters", severity="error")
            return

        result_container = self.query_one("#retrieve-result", Container)
        result_container.remove_children()
        result_container.mount(Static("[yellow]Verifying compliance...[/]"))

        result = await self.client.verify_data(data_hash)

        result_container.remove_children()
        if result:
            if 'error' in result:
                result_container.mount(
                    Static(f"[red]Error: {result['error']}[/]")
                )
            else:
                verified = result.get('verified', False)
                event_type = result.get('event_type', 'unknown')
                if verified:
                    result_container.mount(
                        Static(f"[green]Verified![/] Event type: {event_type}")
                    )
                else:
                    result_container.mount(
                        Static(f"[yellow]Not verified[/] Event type: {event_type}")
                    )
        else:
            result_container.mount(
                Static("[red]Failed to verify data[/]")
            )

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')
        if event_type == 'data.shared':
            data = event.get('data', {})
            self.app.notify(
                f"Data shared: {data.get('data_hash', '')[:16]}...",
                severity="information"
            )

    async def refresh_data(self) -> None:
        """Refresh screen data."""
        pass

    def action_refresh(self) -> None:
        """Handle refresh action."""
        pass
