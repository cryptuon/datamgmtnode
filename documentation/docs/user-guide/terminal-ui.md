# Terminal UI (TUI)

The DataMgmt Node includes a terminal-based user interface built with Python Textual for monitoring and managing your node from the command line.

## Overview

The TUI provides:

- **Real-time monitoring** via WebSocket connection
- **Keyboard navigation** for quick access to all screens
- **Rich terminal rendering** with colors and layouts
- **Low resource usage** compared to web browsers

## Starting the TUI

```bash
# Start the TUI (node must be running)
poetry run python -m datamgmtnode.tui

# Or with custom API URL
poetry run python -m datamgmtnode.tui --api-url http://localhost:8082
```

!!! note
    The node must be running before starting the TUI. The TUI connects to the Dashboard API on port 8082.

## Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `m` | Switch to Main screen |
| `h` | Switch to Health screen |
| `t` | Switch to Tokens screen |
| `x` | Switch to Transfers screen |
| `d` | Switch to Data screen |
| `c` | Switch to Compliance screen |
| `n` | Switch to Network screen |
| `r` | Refresh current screen |
| `q` | Quit application |

## Screens

### Main Screen

The main dashboard provides an overview of node status:

- Node ID and version
- Health status summary
- Recent events
- Quick statistics

**Shortcut:** `m`

### Health Screen

Detailed health monitoring:

- Component status (Blockchain, P2P, Encryption)
- Connection indicators
- Error details if any

**Shortcut:** `h`

### Tokens Screen

Token management:

- View configured tokens
- Check balances
- Token type (native vs ERC-20)

**Shortcut:** `t`

### Transfers Screen

Token transfer history:

- Recent transfers
- Transfer status (completed/failed)
- Transaction hashes

**Shortcut:** `x`

### Data Screen

Data sharing operations:

- Shared data overview
- Data hashes
- Recipient information

**Shortcut:** `d`

### Compliance Screen

Compliance event history:

- Event timeline
- Event types and details
- Verification status

**Shortcut:** `c`

### Network Screen

P2P network information:

- Connected peers list
- Network statistics
- Peer health indicators

**Shortcut:** `n`

## Architecture

### Technology Stack

| Component | Technology |
|-----------|------------|
| **Framework** | Textual 0.x |
| **Styling** | TCSS (Textual CSS) |
| **Transport** | WebSocket + REST API |
| **Python** | 3.10+ |

### Project Structure

```
datamgmtnode/tui/
├── __init__.py
├── app.py                # Main TUI application
├── api_client.py         # Dashboard API client
├── screens/
│   ├── __init__.py
│   ├── main_screen.py    # Main dashboard
│   ├── health_screen.py  # Health status
│   ├── tokens_screen.py  # Token management
│   ├── transfers_screen.py  # Transfer history
│   ├── data_screen.py    # Data operations
│   ├── compliance_screen.py  # Compliance events
│   └── network_screen.py # Network info
├── widgets/
│   └── __init__.py       # Custom widgets
└── styles/
    └── app.tcss          # Application styles
```

### API Client

The TUI uses a dedicated API client that connects to the Dashboard API:

```python
from datamgmtnode.tui.api_client import DashboardClient

client = DashboardClient("http://localhost:8082")

# Connect to WebSocket
await client.connect_websocket()

# Make API requests
health = await client.get_health()
tokens = await client.get_tokens()
peers = await client.get_peers()

# Disconnect
await client.disconnect()
```

## Real-Time Updates

The TUI maintains a WebSocket connection for live updates:

- Automatic reconnection on disconnect
- Event notifications displayed as toast messages
- Screen data refreshes on relevant events

### Event Notifications

Important events trigger notifications:

| Event | Notification |
|-------|--------------|
| `system.error` | Error message displayed |
| `token.transfer_completed` | "Transfer completed" toast |
| `data.shared` | "Data shared" toast |

## Customization

### Styling

The TUI uses TCSS for styling. Modify `styles/app.tcss`:

```css
/* Example customization */
Screen {
    background: $surface;
}

Header {
    background: $primary;
}

.status-healthy {
    color: green;
}

.status-unhealthy {
    color: red;
}
```

### Adding Screens

Create a new screen by extending the base screen class:

```python
from textual.screen import Screen
from textual.widgets import Static

class CustomScreen(Screen):
    def compose(self):
        yield Static("Custom content")

    async def refresh_data(self):
        # Fetch and update data
        pass

    async def handle_event(self, event):
        # Handle WebSocket events
        pass
```

Register in `app.py`:

```python
MODES = {
    # ... existing modes
    "custom": CustomScreen,
}

BINDINGS = [
    # ... existing bindings
    Binding("u", "switch_mode('custom')", "Custom", show=True),
]
```

## Requirements

The TUI requires the Textual library:

```bash
pip install textual
```

Or with Poetry:

```bash
poetry add textual
```

## Troubleshooting

### Connection Failed

**Problem:** "Failed to connect to Dashboard API" warning.

**Causes:**
- Node not running
- Wrong API URL
- Firewall blocking connections

**Solution:**

1. Verify the node is running:
   ```bash
   curl http://localhost:8082/api/health
   ```

2. Check the API URL:
   ```bash
   poetry run python -m datamgmtnode.tui --api-url http://localhost:8082
   ```

### Display Issues

**Problem:** Characters not rendering correctly.

**Solution:** Ensure your terminal supports Unicode and 256 colors:

```bash
# Check terminal capabilities
echo $TERM

# Set if needed
export TERM=xterm-256color
```

### Slow Refresh

**Problem:** Data updates slowly.

**Solution:** Use the `r` key to manually refresh, or check WebSocket connection status in the footer.

## See Also

- [Web Dashboard](web-dashboard.md) - Browser-based interface
- [API Reference](api-reference.md) - Complete API documentation
- [Monitoring](../operations/monitoring.md) - Production monitoring
