"""Compliance history screen for TUI."""

from datetime import datetime
from typing import Any, Dict, List

from textual.app import ComposeResult
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, Label

from datamgmtnode.tui.api_client import DashboardClient


class ComplianceScreen(Screen):
    """Compliance event history screen."""

    BINDINGS = [("r", "refresh", "Refresh")]

    def __init__(self, client: DashboardClient, **kwargs):
        super().__init__(**kwargs)
        self.client = client
        self.history: List[Dict[str, Any]] = []

    def compose(self) -> ComposeResult:
        yield Container(
            Label("Compliance History", id="screen-title"),
            Horizontal(
                Container(
                    Label("Filter by type"),
                    Input(placeholder="e.g., data_share", id="filter-input"),
                    id="filter-input-container"
                ),
                Container(
                    Button("Apply Filter", id="apply-filter-btn", variant="primary"),
                    Button("Clear Filter", id="clear-filter-btn", variant="default"),
                    id="filter-buttons"
                ),
                id="filter-section"
            ),
            Vertical(
                Label("Events", classes="section-title"),
                DataTable(id="compliance-table"),
                id="table-section"
            ),
            Vertical(
                Label("Statistics", classes="section-title"),
                Container(
                    Label("Total Events: 0", id="total-events"),
                    Label("Active Filters: None", id="active-filters"),
                    id="stats-container"
                ),
                id="stats-section"
            ),
            id="compliance-container"
        )

    async def on_mount(self) -> None:
        """Handle screen mount."""
        table = self.query_one("#compliance-table", DataTable)
        table.add_columns("Type", "Hash", "Block", "Tx Hash", "Time")
        table.cursor_type = "row"

        await self.refresh_data()

    async def refresh_data(self, filters: List[str] = None) -> None:
        """Refresh compliance history data."""
        result = await self.client.get_compliance_history(filters)

        if result:
            self.history = result.get('history', [])
            count = result.get('count', 0)
            active_filters = result.get('filters', [])

            # Update table
            table = self.query_one("#compliance-table", DataTable)
            table.clear()

            for event in self.history:
                event_type = event.get('type', 'unknown')
                event_hash = event.get('hash', 'N/A')
                block = str(event.get('block', 'N/A'))
                tx_hash = event.get('tx_hash', 'N/A')

                # Truncate hashes
                display_hash = f"{event_hash[:8]}...{event_hash[-6:]}" if len(event_hash) > 16 else event_hash
                display_tx = f"{tx_hash[:8]}...{tx_hash[-6:]}" if len(tx_hash) > 16 else tx_hash

                # Format timestamp if available
                timestamp = event.get('timestamp')
                if timestamp:
                    time_str = datetime.fromtimestamp(timestamp).strftime('%m/%d %H:%M')
                else:
                    time_str = '-'

                table.add_row(event_type, display_hash, block, display_tx, time_str)

            # Update statistics
            self.query_one("#total-events", Label).update(f"Total Events: {count}")

            filter_str = ", ".join(active_filters) if active_filters else "None"
            self.query_one("#active-filters", Label).update(f"Active Filters: {filter_str}")

    async def on_button_pressed(self, event: Button.Pressed) -> None:
        """Handle button presses."""
        if event.button.id == "apply-filter-btn":
            await self._apply_filter()
        elif event.button.id == "clear-filter-btn":
            await self._clear_filter()

    async def _apply_filter(self) -> None:
        """Apply filter to compliance history."""
        filter_input = self.query_one("#filter-input", Input)
        filter_value = filter_input.value.strip()

        if filter_value:
            filters = [f.strip() for f in filter_value.split(',')]
            await self.refresh_data(filters)
        else:
            await self.refresh_data()

    async def _clear_filter(self) -> None:
        """Clear filter and show all events."""
        self.query_one("#filter-input", Input).value = ""
        await self.refresh_data()

    async def handle_event(self, event: Dict[str, Any]) -> None:
        """Handle WebSocket events."""
        event_type = event.get('type', '')
        if event_type == 'compliance.event':
            # Add new event to the table
            data = event.get('data', {})
            table = self.query_one("#compliance-table", DataTable)

            event_type_val = data.get('type', 'unknown')
            event_hash = data.get('hash', 'N/A')
            block = str(data.get('block', 'N/A'))
            tx_hash = data.get('tx_hash', 'N/A')

            display_hash = f"{event_hash[:8]}...{event_hash[-6:]}" if len(event_hash) > 16 else event_hash
            display_tx = f"{tx_hash[:8]}...{tx_hash[-6:]}" if len(tx_hash) > 16 else tx_hash

            timestamp = data.get('timestamp')
            time_str = datetime.fromtimestamp(timestamp).strftime('%m/%d %H:%M') if timestamp else '-'

            # Add at the beginning
            table.add_row(event_type_val, display_hash, block, display_tx, time_str)

            # Update count
            current_label = self.query_one("#total-events", Label)
            try:
                current_text = str(current_label.renderable)
                current_count = int(current_text.split(': ')[1])
                current_label.update(f"Total Events: {current_count + 1}")
            except (ValueError, IndexError):
                pass

    def action_refresh(self) -> None:
        """Handle refresh action."""
        self.app.run_worker(self.refresh_data())
