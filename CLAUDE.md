# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a WhatsApp MCP (Model Context Protocol) server that enables AI assistants to interact with WhatsApp. It consists of two main components:

1. **Go WhatsApp Bridge** (`whatsapp-bridge/`): Connects to WhatsApp Web API, handles authentication, and maintains a local SQLite database of messages
2. **Python MCP Server** (`whatsapp-mcp-server/`): Implements the MCP protocol to provide WhatsApp functionality as tools for AI assistants

## Common Development Commands

### Go WhatsApp Bridge
```bash
# Run the WhatsApp bridge (from whatsapp-bridge/ directory)
go run main.go

# Build the WhatsApp bridge
go build -o whatsapp-bridge main.go

# Run with custom storage path
go run main.go -storage-path="/custom/path"
```

### Python MCP Server
```bash
# Run the MCP server (from whatsapp-mcp-server/ directory)  
uv run main.py

# Install/sync dependencies
uv sync

# Update dependencies lock file
uv lock
```

## Architecture and Key Components

### Go WhatsApp Bridge (`whatsapp-bridge/main.go`)
- **MessageStore**: Manages SQLite database for message history (tables: `chats`, `messages`)
- **HTTP API Server** (port 8080): Provides endpoints for the Python MCP server
  - `/contacts` - Search contacts
  - `/messages` - Query message history
  - `/chats` - List chats
  - `/send-message` - Send WhatsApp messages
  - `/send-file` - Send media files
  - `/download-media` - Download media from messages
  - `/group/*` - Group management endpoints
- **WhatsApp Client**: Uses `whatsmeow` library for WhatsApp Web multidevice API
- **Media Handling**: Supports images, videos, documents, audio messages
- **Storage**: Default path is `./store/`, contains:
  - `messages.db` - Message history database
  - `whatsapp.db` - WhatsApp session data
  - Media files organized by chat JID

### Python MCP Server (`whatsapp-mcp-server/`)
- **main.py**: MCP server implementation using FastMCP
- **whatsapp.py**: Core WhatsApp functionality that communicates with Go bridge
- **audio.py**: Audio processing utilities for voice messages
- **MCP Tools Exposed**:
  - Contact management: `search_contacts`, `get_contact_chats`
  - Message operations: `list_messages`, `send_message`, `get_message_context`
  - Chat operations: `list_chats`, `get_chat`, `get_direct_chat_by_contact`
  - Media handling: `send_file`, `send_audio_message`, `download_media`
  - Group management: `create_group`, `join_group_with_link`, `leave_group`, etc.

### Data Flow
1. MCP client (Claude) → Python MCP server → Go HTTP API → WhatsApp Web API
2. Messages are stored in SQLite and indexed for efficient searching
3. Media files are downloaded on-demand and stored locally

## Important Notes

- The Go bridge must be running before starting the Python MCP server
- First run requires QR code authentication via WhatsApp mobile app
- Re-authentication needed approximately every 20 days
- Windows requires CGO enabled and a C compiler (see README for details)
- Media is stored as metadata by default; use `download_media` to fetch actual files
- Audio messages require `.ogg` Opus format (automatic conversion with FFmpeg)

## Database Schema

### chats table
- `jid` (PRIMARY KEY): WhatsApp JID identifier
- `name`: Chat/contact name
- `last_message_time`: Timestamp of last message

### messages table
- `id`, `chat_jid` (COMPOSITE PRIMARY KEY)
- `sender`, `content`, `timestamp`, `is_from_me`
- `media_type`, `filename`, `url`
- `media_key`, `file_sha256`, `file_enc_sha256`, `file_length` (for media)

## Current Feature Branch

Working on `variant-data-folder-in-mcp-server` - implementing custom attachment and database storage paths.