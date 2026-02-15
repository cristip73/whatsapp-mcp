# CLAUDE.md

This file provides guidance to Claude Code when working with this repository. For full installation and setup instructions, see **README.md**.

## Project Overview

WhatsApp MCP server that enables AI assistants to interact with WhatsApp. Two components:

1. **Go WhatsApp Bridge** (`whatsapp-bridge/`): Connects to WhatsApp Web API via `whatsmeow`, maintains SQLite database, exposes HTTP API on port 8080
2. **Python MCP Server** (`whatsapp-mcp-server/`): Implements MCP protocol using FastMCP, provides WhatsApp tools to AI clients

### Data Flow
```
MCP Client (Claude/Cursor) → Python MCP Server (stdio) → Go HTTP API (:8080) → WhatsApp Web API
                                        ↕ shared data folder ↕
                              messages.db + whatsapp.db + media files
```

Both components share a **data folder** (configured via `-storage-path` for Go and `--attachments-path` for Python). This folder contains `messages.db`, `whatsapp.db`, and downloaded media organized by chat JID.

## Development Commands

### Go WhatsApp Bridge
```bash
cd whatsapp-bridge
go build -o whatsapp-bridge main.go          # Build
./whatsapp-bridge -storage-path="$HOME/Documents/WhatsApp-MCP-Data"  # Run
```

### Python MCP Server
```bash
cd whatsapp-mcp-server
uv sync                                      # Install/sync dependencies
uv run main.py --attachments-path="$HOME/Documents/WhatsApp-MCP-Data"  # Run
```

## MCP Client Configuration (`.mcp.json`)

To use this MCP server in a project, create a `.mcp.json` file in the project root:

```json
{
  "mcpServers": {
    "whatsapp": {
      "command": "/opt/homebrew/bin/uv",
      "args": [
        "run",
        "--directory",
        "/ABSOLUTE/PATH/TO/whatsapp-mcp/whatsapp-mcp-server",
        "main.py",
        "--attachments-path",
        "/ABSOLUTE/PATH/TO/WhatsApp-MCP-Data"
      ]
    }
  }
}
```

**Paths to replace:**
- `command`: result of `which uv`
- `--directory`: absolute path to the `whatsapp-mcp-server/` folder
- `--attachments-path`: same folder as the Go bridge's `-storage-path`

**Where to save:**
- **Claude Code**: `.mcp.json` in project root (already gitignored)
- **Claude Desktop**: add to `~/Library/Application Support/Claude/claude_desktop_config.json`
- **Cursor**: add to `~/.cursor/mcp.json`

## Architecture

### MCP Tools — Progressive Disclosure

The server uses **hybrid progressive disclosure**: 6 tools exposed directly, 8 hidden tool groups discoverable via meta-tools.

**4 direct tools** (always visible to the LLM):
- `search_contacts` — search by name or phone
- `list_messages` — query messages with filters, pagination, context
- `list_chats` — list chats sorted by activity or name
- `send_message` — multi-action: text, file, audio, reply, broadcast

**2 meta-tools** (progressive disclosure):
- `search_tools(query)` — discover hidden tools by keyword
- `execute_tool(tool_name, params)` — run a hidden tool

**8 hidden tool groups** (via `search_tools` → `execute_tool`):
- `download_media` — download media files from messages
- `get_chat_info` — chat/contact lookup (5 actions)
- `message_action` — react, edit, delete, mark read, poll (5 actions)
- `manage_group` — create, join, leave, settings, participants (12 actions)
- `search_messages` — message context, cross-group search (2 actions)
- `analytics` — group activity, engagement, journey, overlap (4 actions)
- `manage_profile` — presence, about, status, registration check (4 actions)
- `manage_channel` — newsletters, communities, sub-groups (6 actions)

### Go HTTP API (`whatsapp-bridge/main.go`)

Single file. All endpoints under `/api/` prefix on port 8080. Key routes:
- `/api/send` — send text/media messages
- `/api/download` — download media from messages
- `/api/create_group`, `/api/join_group`, `/api/leave_group` — group lifecycle
- `/api/get_group_info`, `/api/get_group_invite_link` — group queries
- `/api/update_group_participants` — add/remove/promote/demote
- `/api/set_group_*` — group settings (name, topic, photo, announce, locked, join_approval)
- `/api/send_reaction`, `/api/edit_message`, `/api/delete_message`, `/api/mark_read`
- `/api/create_poll`, `/api/send_reply`
- `/api/send_presence`, `/api/set_status_message`, `/api/send_status`
- `/api/create_newsletter`, `/api/get_newsletters`, `/api/newsletter_send`
- `/api/link_group`, `/api/unlink_group`, `/api/get_sub_groups`
- `/api/is_on_whatsapp`, `/api/get_contact_groups`

### Python MCP Server (`whatsapp-mcp-server/`)

- **main.py**: MCP server — tool definitions, hidden tool registry, progressive disclosure logic
- **whatsapp.py**: Core WhatsApp functions (50+ functions), communicates with Go bridge HTTP API and reads directly from shared SQLite database
- **audio.py**: Audio conversion to `.ogg` Opus format (requires FFmpeg)

### Database Schema

**chats table**: `jid` (PK), `name`, `last_message_time`

**messages table**: `id` + `chat_jid` (composite PK), `sender`, `content`, `timestamp`, `is_from_me`, `media_type`, `filename`, `url`, `media_key`, `file_sha256`, `file_enc_sha256`, `file_length`

**Indexes**: `idx_messages_chat_timestamp` (chat_jid, timestamp), `idx_messages_sender` (sender), `idx_chats_name` (name)

## Important Notes

- Go bridge must be running before using MCP server
- First run requires QR code scan (WhatsApp → Linked Devices → Link a Device)
- Sessions expire ~20 days — re-scan QR code when that happens
- `--attachments-path` (Python) and `-storage-path` (Go) must point to the **same folder**
- Media stored as metadata only; use `download_media` tool to fetch actual files
- Audio voice messages require `.ogg` Opus format; FFmpeg auto-converts other formats
- Windows requires CGO enabled and a C compiler (see README.md)
