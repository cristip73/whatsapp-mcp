# WhatsApp MCP Server

This is a Model Context Protocol (MCP) server for WhatsApp.

> **Note**: This is a personal fork of the [original WhatsApp MCP project](https://github.com/lharries/whatsapp-mcp) by lharries.

With this you can search and read your personal Whatsapp messages (including images, videos, documents, and audio messages), search your contacts and send messages to either individuals or groups. You can also send media files including images, videos, documents, and audio messages.

It connects to your **personal WhatsApp account** directly via the Whatsapp web multidevice API (using the [whatsmeow](https://github.com/tulir/whatsmeow) library). All your messages are stored locally in a SQLite database and only sent to an LLM (such as Claude) when the agent accesses them through tools (which you control).

Here's an example of what you can do when it's connected to Claude.

![WhatsApp MCP](./example-use.png)

> To get updates on this and other projects I work on [enter your email here](https://docs.google.com/forms/d/1rTF9wMBTN0vPfzWuQa2BjfGKdKIpTbyeKxhPMcEzgyI/preview)

## Installation

### Prerequisites

- **Go** (1.21+)
- **Python** 3.10+
- **UV** (Python package manager): `curl -LsSf https://astral.sh/uv/install.sh | sh`
- **An MCP client**: Claude Code, Claude Desktop, or Cursor
- **FFmpeg** (_optional_) — only needed if you want to send audio files as playable WhatsApp voice messages. Without it, audio files are sent as regular file attachments.

### Step 1: Clone and build

```bash
git clone https://github.com/cristip73/whatsapp-mcp.git
cd whatsapp-mcp

# Build the Go bridge binary
cd whatsapp-bridge
go build -o whatsapp-bridge main.go
cd ..
```

### Step 2: Create a data folder

The bridge and MCP server share a **data folder** where everything is stored:
- `messages.db` — your WhatsApp message history (SQLite database)
- `whatsapp.db` — your WhatsApp session/authentication data
- Downloaded media files (photos, videos, documents), organized by chat

Both the Go bridge (`-storage-path`) and the Python MCP server (`--attachments-path`) must point to **the same folder**.

Create it somewhere persistent, for example in your Documents folder:

```bash
mkdir -p ~/Documents/WhatsApp-MCP-Data
```

You'll use this path in the next steps. In the examples below, we use `~/Documents/WhatsApp-MCP-Data` — replace it with your chosen path.

### Step 3: Authenticate with WhatsApp

Run the bridge **manually in a terminal** so you can see the QR code:

```bash
cd whatsapp-bridge
./whatsapp-bridge -storage-path="$HOME/Documents/WhatsApp-MCP-Data"
```

1. A QR code appears in the terminal
2. On your phone: open WhatsApp → Settings → Linked Devices → Link a Device
3. Scan the QR code
4. Wait until you see `Connected to WhatsApp`
5. Press `Ctrl+C` to stop

The session is now saved in your data folder. The bridge can run headless (without a terminal) from now on.

> **Re-authentication**: Sessions expire after ~20 days. When that happens, stop the background bridge and repeat this step to scan a new QR code.

### Step 4: Run the bridge in the background

The bridge needs to be running whenever you want to use WhatsApp through your MCP client. You have two options:

#### Option A: Run manually in a terminal

Simple, but the bridge stops when you close the terminal:

```bash
./whatsapp-bridge -storage-path="$HOME/Documents/WhatsApp-MCP-Data"
```

#### Option B: macOS background service (recommended)

Set up `launchd` so the bridge starts on login, restarts on crash, and runs independently of any terminal.

**Create the file** `~/Library/LaunchAgents/com.whatsapp-bridge.plist` with this content:

```xml
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN"
        "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.whatsapp-bridge</string>

    <key>ProgramArguments</key>
    <array>
        <string>/Users/YOUR_USERNAME/path/to/whatsapp-mcp/whatsapp-bridge/whatsapp-bridge</string>
        <string>-storage-path</string>
        <string>/Users/YOUR_USERNAME/Documents/WhatsApp-MCP-Data</string>
    </array>

    <key>WorkingDirectory</key>
    <string>/Users/YOUR_USERNAME/path/to/whatsapp-mcp/whatsapp-bridge</string>

    <key>StandardOutPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/whatsapp-bridge.log</string>
    <key>StandardErrorPath</key>
    <string>/Users/YOUR_USERNAME/Library/Logs/whatsapp-bridge.err</string>

    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <true/>
</dict>
</plist>
```

Replace all occurrences of `YOUR_USERNAME` and adjust the repo path. All paths must be **absolute** (no `~` or `$HOME`).

**Start the service:**

```bash
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.whatsapp-bridge.plist
```

**Useful commands:**

```bash
# Restart the bridge (e.g. after rebuilding the binary or re-authenticating)
launchctl bootout gui/$(id -u)/com.whatsapp-bridge
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.whatsapp-bridge.plist

# Check if it's running
lsof -i :8080

# View logs
tail -f ~/Library/Logs/whatsapp-bridge.log
```

**When re-authentication is needed (~every 20 days):**

1. Stop the service: `launchctl bootout gui/$(id -u)/com.whatsapp-bridge`
2. Run manually in terminal to scan QR code (step 3)
3. Restart the service: `launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.whatsapp-bridge.plist`

**Linux:** Use a systemd user service instead of launchd. **Windows:** See the Windows section below.

### Step 5: Configure the MCP server

The MCP server is what connects your AI client (Claude, Cursor) to the bridge. It runs automatically when your client starts — you just need to tell the client where to find it.

Create a `.mcp.json` configuration file. Here's a **complete example** — you need to replace 3 paths:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--directory",
        "/Users/YOUR_USERNAME/path/to/whatsapp-mcp/whatsapp-mcp-server",
        "main.py",
        "--attachments-path",
        "/Users/YOUR_USERNAME/Documents/WhatsApp-MCP-Data"
      ]
    }
  }
}
```

**How to find the paths:**

| Placeholder | How to find it | Example |
|---|---|---|
| `command` (path to `uv`) | Run `which uv` in terminal | `/opt/homebrew/bin/uv` |
| `--directory` (path to MCP server) | From the repo root, it's the `whatsapp-mcp-server` subfolder | `/Users/jane/Code/whatsapp-mcp/whatsapp-mcp-server` |
| `--attachments-path` (data folder) | The same folder from step 2 | `/Users/jane/Documents/WhatsApp-MCP-Data` |

> **Important**: The `--attachments-path` must be the same folder as the bridge's `-storage-path`. This is how the MCP server finds the message database and downloaded media.

**Where to save this file:**

- **Claude Code**: Save as `.mcp.json` in the repository root (already gitignored)
- **Claude Desktop**: Add the `whatsapp` entry to `~/Library/Application Support/Claude/claude_desktop_config.json` (macOS) or `%APPDATA%\Claude\claude_desktop_config.json` (Windows)
- **Cursor**: Add the entry to `~/.cursor/mcp.json`

### Step 6: Restart your client

Restart Claude Desktop, Cursor, or re-enter the project directory in Claude Code to pick up the new MCP configuration. You should see WhatsApp tools appear in your client's tool list.

### Windows notes

`go-sqlite3` requires **CGO enabled** and a C compiler, which are not available by default on Windows.

1. **Install a C compiler** using [MSYS2](https://www.msys2.org/), then add `ucrt64\bin` to your PATH ([guide](https://code.visualstudio.com/docs/cpp/config-mingw))

2. **Enable CGO and build:**

   ```bash
   cd whatsapp-bridge
   go env -w CGO_ENABLED=1
   go build -o whatsapp-bridge.exe main.go
   ```

Without this, you'll see: `Binary was compiled with 'CGO_ENABLED=0', go-sqlite3 requires cgo to work.`

## Architecture Overview

The system has two components that share a data folder:

```
┌──────────────┐      HTTP API       ┌──────────────────┐     WhatsApp Web
│  MCP Client  │ ──── (MCP) ──────── │  Python MCP      │     API (whatsmeow)
│  (Claude,    │                     │  Server           │
│   Cursor)    │                     │  (whatsapp-mcp-   │         ┌──────────┐
└──────────────┘                     │   server/)        │ ──────  │  Go      │
                                     └────────┬─────────┘         │  Bridge  │
                                              │                    │  (runs   │
                                              │ shared             │  24/7)   │
                                              │ data folder        └────┬─────┘
                                              │                         │
                                              ▼                         ▼
                                     ┌──────────────────────────────────────┐
                                     │  ~/Documents/WhatsApp-MCP-Data/     │
                                     │  ├── messages.db  (message history) │
                                     │  ├── whatsapp.db  (session data)   │
                                     │  └── media files  (by chat JID)    │
                                     └──────────────────────────────────────┘
```

1. **Go WhatsApp Bridge** (`whatsapp-bridge/`): Connects to WhatsApp Web, receives messages in real-time, stores them in SQLite, and exposes an HTTP API on port 8080. Runs continuously in the background.

2. **Python MCP Server** (`whatsapp-mcp-server/`): Implements the MCP protocol. Launched on-demand by your AI client. Reads messages from the shared SQLite database and sends messages through the Go bridge's HTTP API.

## Usage

Once connected, you can interact with your WhatsApp contacts through Claude, leveraging Claude's AI capabilities in your WhatsApp conversations.

### MCP Tools

The server uses a **hybrid progressive disclosure** pattern: 6 tools are directly exposed, while additional tools are discoverable via meta-tools. This keeps the tool list clean for AI assistants while still providing full functionality.

**Directly exposed tools:**

- **search_contacts**: Search for contacts by name or phone number
- **list_messages**: Retrieve messages with optional filters, pagination, and surrounding context
- **list_chats**: List chats with metadata, sorted by last activity or name
- **send_message**: Multi-action tool for sending text, files, audio, replies, and broadcasts

**Meta-tools (progressive disclosure):**

- **search_tools**: Discover additional tools by keyword (e.g. `search_tools("react")`, `search_tools("group settings")`)
- **execute_tool**: Run a tool found via `search_tools`

Hidden tools cover: media download, chat/contact lookup, message actions (react, edit, delete, read receipts, polls), group management (create, join, leave, settings, participants), cross-group message search, analytics & engagement reports, profile/presence, and channels/newsletters.

### Media Handling Features

The MCP server supports both sending and receiving various media types:

#### Media Sending

You can send various media types to your WhatsApp contacts:

- **Images, Videos, Documents**: Use `send_message` with `action: "file"` to share any supported media type.
- **Voice Messages**: Use `send_message` with `action: "audio"` to send audio files as playable WhatsApp voice messages.
  - For optimal compatibility, audio files should be in `.ogg` Opus format.
  - With FFmpeg installed, the system will automatically convert other audio formats (MP3, WAV, etc.) to the required format.
  - Without FFmpeg, you can still send raw audio files using `send_message` with `action: "file"`, but they won't appear as playable voice messages.

#### Media Downloading

By default, only media metadata is stored in the local database. The message will indicate that media was sent. To access the actual file, use `search_tools("download")` to find the download tool, then call it via `execute_tool` with `message_id` and `chat_jid` (shown in messages containing media). This downloads the file and returns the local path.

## Technical Details

1. Claude sends requests to the Python MCP server
2. The MCP server queries the Go bridge's HTTP API or reads directly from the shared SQLite database
3. The Go bridge connects to the WhatsApp Web API and keeps the SQLite database up to date
4. Data flows back through the chain to Claude
5. When sending messages, the request flows from Claude through the MCP server to the Go bridge and to WhatsApp
6. Both components share a storage directory (configurable via `--storage-path` / `--attachments-path`)

## Troubleshooting

- If you encounter permission issues when running uv, you may need to add it to your PATH or use the full path to the executable.
- Make sure both the Go application and the Python server are running for the integration to work properly.

### Authentication Issues

- **QR Code Not Displaying**: If the QR code doesn't appear, try restarting the authentication script. If issues persist, check if your terminal supports displaying QR codes.
- **WhatsApp Already Logged In**: If your session is already active, the Go bridge will automatically reconnect without showing a QR code.
- **Device Limit Reached**: WhatsApp limits the number of linked devices. If you reach this limit, you'll need to remove an existing device from WhatsApp on your phone (Settings > Linked Devices).
- **No Messages Loading**: After initial authentication, it can take several minutes for your message history to load, especially if you have many chats.
- **WhatsApp Out of Sync**: If your WhatsApp messages get out of sync with the bridge, delete both database files (`messages.db` and `whatsapp.db`) from your storage directory (default: `whatsapp-bridge/store/`) and restart the bridge to re-authenticate.

For additional Claude Desktop integration troubleshooting, see the [MCP documentation](https://modelcontextprotocol.io/quickstart/server#claude-for-desktop-integration-issues). The documentation includes helpful tips for checking logs and resolving common issues.
