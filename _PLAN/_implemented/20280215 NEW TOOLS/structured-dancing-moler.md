# Plan Complet: WhatsApp MCP - Bug Fixes + 28 New Tools

## Context

Proiectul WhatsApp MCP server (Go bridge + Python MCP) are 20 tools implementate. Acest plan adauga 22 tools noi si fixeaza 4 buguri, transformand MCP-ul dintr-un tool de mesagerie intr-o **platforma de management coaching**.

**Fisiere principale de modificat:**
- `whatsapp-bridge/main.go` - Go bridge (endpoints HTTP + business logic)
- `whatsapp-mcp-server/whatsapp.py` - Python backend (functii wrapper)
- `whatsapp-mcp-server/main.py` - MCP tool definitions

**Surse de referinta pentru agenti:**
- Go bridge patterns: `/private/tmp/claude-501/-Users-cristi-Downloads-CODING-whatsapp-mcp/tasks/ad020b0.output`
- Python MCP patterns: `/private/tmp/claude-501/-Users-cristi-Downloads-CODING-whatsapp-mcp/tasks/af57273.output`
- whatsmeow API signatures: `/private/tmp/claude-501/-Users-cristi-Downloads-CODING/whatsapp-mcp/tasks/a31f4d8.output`
- Roadmap/feature list: `/Users/cristi/Downloads/CODING/whatsapp-mcp/WHATSAPP_MCP_ROADMAP.md`

---

## Coding Standards (OBLIGATORIU pentru toti agentii)

### Go Bridge Pattern (main.go)

Fiecare nou tool urmeaza EXACT acest pattern:

**1. Request/Response structs** (adaugat inainte de `// Store additional media info` ~linia 912):
```go
type XxxRequest struct {
    FieldName string `json:"field_name"`
}
type XxxResponse struct {
    Success bool   `json:"success"`
    Message string `json:"message"`
    Data    string `json:"data,omitempty"`  // optional fields cu omitempty
}
```

**2. Business logic function** (adaugat dupa `getContactGroups`, inainte de `// Extract media info`):
```go
func xxxFunction(client *whatsmeow.Client, param string) (bool, string, <optional extra returns>) {
    if !client.IsConnected() {
        return false, "Not connected to WhatsApp", ...
    }
    // Parse JID daca e nevoie:
    jid, err := parsePhoneOrJID(param)  // sau types.ParseJID(param) pt group JIDs
    if err != nil {
        return false, fmt.Sprintf("invalid JID: %v", err), ...
    }
    // Apel whatsmeow - MEREU cu context.Background():
    result, err := client.XxxMethod(context.Background(), jid, ...)
    if err != nil {
        return false, fmt.Sprintf("failed to xxx: %v", err), ...
    }
    return true, "success message", ...
}
```

**3. HTTP handler** (adaugat inainte de `// Start the server`):
```go
http.HandleFunc("/api/xxx", func(w http.ResponseWriter, r *http.Request) {
    if r.Method != http.MethodPost {
        http.Error(w, "Method not allowed", http.StatusMethodNotAllowed)
        return
    }
    var req XxxRequest
    if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
        http.Error(w, "Invalid request format", http.StatusBadRequest)
        return
    }
    if req.RequiredField == "" {
        http.Error(w, "required_field is required", http.StatusBadRequest)
        return
    }
    success, msg, data := xxxFunction(client, req.RequiredField)
    w.Header().Set("Content-Type", "application/json")
    if !success {
        w.WriteHeader(http.StatusInternalServerError)
    }
    json.NewEncoder(w).Encode(XxxResponse{Success: success, Message: msg, Data: data})
})
```

### Python Pattern (whatsapp.py + main.py)

**whatsapp.py - HTTP API wrapper** (adaugat grupat cu functiile similare):
```python
def new_function(param: str) -> Tuple[bool, str]:
    """Brief description."""
    try:
        url = f"{WHATSAPP_API_BASE_URL}/endpoint_name"
        payload = {"param": param}
        response = requests.post(url, json=payload)
        if response.status_code == 200:
            result = response.json()
            return result.get("success", False), result.get("message", "Unknown error")
        else:
            return False, f"HTTP {response.status_code}: {response.text}"
    except requests.RequestException as e:
        return False, f"Request error: {str(e)}"
```

**main.py - MCP tool** (adaugat grupat cu tools similare):
```python
@mcp.tool()
def new_tool(param: str) -> Dict[str, Any]:
    """Brief description.

    Args:
        param: Parameter description
    """
    success, message = whatsapp_new_function(param)
    return {"success": success, "message": message}
```

### Reguli stricte:
- **Nu adauga imports noi** decat daca sunt absolut necesare
- **Pastreaza ordinea**: structs -> business logic -> handlers (Go); functions grupate logic (Python)
- **Toate apelurile whatsmeow** folosesc `context.Background()`
- **Toate JID-urile de grup** se parseaza cu `types.ParseJID()`, nu `parsePhoneOrJID()`
- **Error messages** incep cu lower case, fara punct final
- **JSON tags** folosesc snake_case
- **Nu adauga logging/print** in exces - doar erori

---

## Faza 0: Bug Fixes

### BF-1: Fix double file:// in download_media
**Fisier:** `whatsapp-mcp-server/main.py` linia 259
**Fix:** Sterge `file://` prefix din main.py (pastreaza-l doar in whatsapp.py care deja returneaza path fara prefix)
**Actual:** `whatsapp.py:804` returneaza `path` (fara prefix), apoi `main.py:259` adauga `file://` - e corect!
**Re-check:** Citeste whatsapp.py:798-804 si main.py:255-259. Daca whatsapp.py NU adauga file://, atunci main.py e corect. Bug-ul e ca whatsapp.py:801-802 printeaza cu file:// (cosmetic print) dar returneaza path fara prefix. **Nu e un bug real in functionalitate, doar in print.** Sterge print-ul cosmetic din whatsapp.py:801-802.

### BF-2: Adauga DB indexes
**Fisier:** `whatsapp-bridge/main.go` in functia `NewMessageStore` dupa CREATE TABLE
**Adauga:**
```sql
CREATE INDEX IF NOT EXISTS idx_messages_chat_timestamp ON messages(chat_jid, timestamp);
CREATE INDEX IF NOT EXISTS idx_messages_sender ON messages(sender);
CREATE INDEX IF NOT EXISTS idx_chats_name ON chats(name);
```

### BF-3: Fix list_messages return type (OPTIONAL - skip daca risca sa strice MCP)
Lasa cum e - MCP-ul functioneaza cu string-ul formatat. Schimbarea ar putea strica integrarea existenta.

### BF-4: N+1 query optimization (OPTIONAL - nice to have)
Skip pentru acum - prioritizeaza tools noi.

---

## Faza 1: Go Bridge - Toate Endpoint-urile Noi

Toate adaugarile merg in `whatsapp-bridge/main.go`. Impartite in 3 work packages care se executa SECVENTIAL (acelasi fisier):

### WP-GO-1: Group Info & Management (7 endpoints)

**1. `/api/get_group_info`** - Get group metadata + participant list
- Request: `{ "jid": "group@g.us" }`
- Response: `{ "success": true, "message": "...", "group": { "jid": "...", "name": "...", "topic": "...", "announce": bool, "locked": bool, "participants": [{"jid": "...", "phone": "...", "name": "...", "is_admin": bool}] } }`
- whatsmeow: `client.GetGroupInfo(ctx, jid)` -> `*types.GroupInfo` (group.go:591)
- GroupInfo contine: JID, Name (din GroupName.Name), Topic (din GroupTopic.Topic), IsAnnounce, IsLocked, Participants []GroupParticipant
- GroupParticipant contine: JID, PhoneNumber, LID, IsAdmin, IsSuperAdmin, DisplayName

**2. `/api/get_group_invite_link`** - Get/reset invite link
- Request: `{ "jid": "group@g.us", "reset": false }`
- Response: `{ "success": true, "message": "...", "link": "https://chat.whatsapp.com/xxx" }`
- whatsmeow: `client.GetGroupInviteLink(ctx, jid, reset)` (group.go:393) -> `(string, error)`

**3. `/api/set_group_topic`** - Set group description
- Request: `{ "jid": "group@g.us", "topic": "New description" }`
- Response: BasicResponse
- whatsmeow: `client.SetGroupDescription(ctx, jid, description)` (group.go:1053) -> `error`
- NOTE: SetGroupTopic necesita previousID/newID complicate. Foloseste `SetGroupDescription` care e mai simplu.

**4. `/api/set_group_announce`** - Toggle admin-only messaging
- Request: `{ "jid": "group@g.us", "announce": true }`
- Response: BasicResponse
- whatsmeow: `client.SetGroupAnnounce(ctx, jid, announce)` (group.go:381) -> `error`

**5. `/api/set_group_locked`** - Toggle admin-only info edit
- Request: `{ "jid": "group@g.us", "locked": true }`
- Response: BasicResponse
- whatsmeow: `client.SetGroupLocked(ctx, jid, locked)` (group.go:371) -> `error`

**6. `/api/set_group_join_approval`** - Toggle join approval mode
- Request: `{ "jid": "group@g.us", "mode": true }`
- Response: BasicResponse
- whatsmeow: `client.SetGroupJoinApprovalMode(ctx, jid, mode)` (group.go:1018) -> `error`

**7. `/api/is_on_whatsapp`** - Check if phone numbers are on WhatsApp
- Request: `{ "phones": ["+40730883388", "+40720666029"] }`
- Response: `{ "success": true, "message": "...", "results": [{"phone": "...", "is_on_whatsapp": true, "jid": "..."}] }`
- whatsmeow: `client.IsOnWhatsApp(ctx, phones)` (user.go:168) -> `([]types.IsOnWhatsAppResponse, error)`
- IsOnWhatsAppResponse: Query, JID, IsIn (bool)

### WP-GO-2: Message Operations (6 endpoints)

**8. `/api/send_reaction`** - React to a message
- Request: `{ "chat_jid": "...", "sender_jid": "...", "message_id": "...", "reaction": "🔥" }`
- Response: BasicResponse
- whatsmeow: `msg := client.BuildReaction(chat, sender, id, reaction)` (send.go:524)
  apoi `client.SendMessage(ctx, chat, msg)`
- sender_jid = JID-ul celui care a trimis mesajul original. Pentru mesajele proprii, se foloseste `client.Store.ID`
- Reaction gol ("") = remove reaction

**9. `/api/edit_message`** - Edit a sent message
- Request: `{ "chat_jid": "...", "message_id": "...", "new_text": "..." }`
- Response: BasicResponse
- whatsmeow: `newContent := &waE2E.Message{Conversation: proto.String(newText)}`
  `msg := client.BuildEdit(chat, id, newContent)` (send.go:588)
  apoi `client.SendMessage(ctx, chat, msg)`

**10. `/api/delete_message`** - Revoke/delete a message
- Request: `{ "chat_jid": "...", "sender_jid": "...", "message_id": "..." }`
- Response: BasicResponse
- whatsmeow: `msg := client.BuildRevoke(chat, sender, id)` (send.go:509)
  apoi `client.SendMessage(ctx, chat, msg)`
- Pentru mesaje proprii: sender = client.Store.ID

**11. `/api/mark_read`** - Mark messages as read
- Request: `{ "chat_jid": "...", "sender_jid": "...", "message_ids": ["id1", "id2"] }`
- Response: BasicResponse
- whatsmeow: `client.MarkRead(ctx, ids, time.Now(), chat, sender)` (receipt.go:194)

**12. `/api/create_poll`** - Create a WhatsApp poll
- Request: `{ "chat_jid": "...", "question": "...", "options": ["A", "B", "C"], "max_selections": 1 }`
- Response: BasicResponse (cu message_id)
- whatsmeow: Construieste `waE2E.PollCreationMessage` cu:
  - `Name`: question
  - `Options`: []PollCreationMessage_Option cu `OptionName`
  - `SelectableOptionsCount`: max_selections (uint32)
  - `EncKey`: 32 bytes random (crypto/rand)
- Apoi: `client.SendMessage(ctx, chat, &waE2E.Message{PollCreationMessage: pollMsg})`
- IMPORTANT: Trebuie import `"crypto/rand"` si generat encKey de 32 bytes

**13. `/api/send_reply`** - Reply to a specific message
- Request: `{ "chat_jid": "...", "quoted_message_id": "...", "quoted_sender_jid": "...", "message": "...", "quoted_content": "..." }`
- Response: BasicResponse
- whatsmeow: Construieste mesaj cu ContextInfo:
  ```go
  msg := &waE2E.Message{
      ExtendedTextMessage: &waE2E.ExtendedTextMessage{
          Text: proto.String(message),
          ContextInfo: &waE2E.ContextInfo{
              StanzaID:      proto.String(quotedMessageID),
              Participant:   proto.String(quotedSenderJID),
              QuotedMessage: &waE2E.Message{Conversation: proto.String(quotedContent)},
          },
      },
  }
  client.SendMessage(ctx, chat, msg)
  ```

### WP-GO-3: Advanced Features (5 endpoints)

**14. `/api/send_presence`** - Set online/offline
- Request: `{ "presence": "available" }` (sau "unavailable")
- Response: BasicResponse
- whatsmeow: `client.SendPresence(ctx, types.PresenceAvailable)` (presence.go:64)

**15. `/api/set_status_message`** - Change "About" text
- Request: `{ "message": "New status" }`
- Response: BasicResponse
- whatsmeow: `client.SetStatusMessage(ctx, msg)` (user.go:153)

**16. `/api/create_newsletter`** - Create WhatsApp Channel
- Request: `{ "name": "Channel Name", "description": "..." }`
- Response: `{ "success": true, "message": "...", "jid": "...", "name": "..." }`
- whatsmeow: `client.CreateNewsletter(ctx, CreateNewsletterParams{Name, Description})` (newsletter.go:314)
- Returneza `*types.NewsletterMetadata`

**17. `/api/get_newsletters`** - List subscribed newsletters
- Request: `{}` (empty body)
- Response: `{ "success": true, "newsletters": [{"jid": "...", "name": "...", "description": "..."}] }`
- whatsmeow: `client.GetSubscribedNewsletters(ctx)` (newsletter.go:290)

**18. `/api/newsletter_send`** - Send message to newsletter
- Request: `{ "jid": "newsletter_jid@newsletter", "message": "..." }`
- Response: BasicResponse
- Se trimite ca mesaj normal: `client.SendMessage(ctx, newsletterJID, &waE2E.Message{Conversation: proto.String(msg)})`

**19. `/api/send_status`** - Post to WhatsApp Status (stories, 24h)
- Request: `{ "message": "Motivational quote of the day" }`
- Response: BasicResponse
- whatsmeow: `client.SendMessage(ctx, types.StatusBroadcastJID, &waE2E.Message{Conversation: proto.String(msg)})`
- `types.StatusBroadcastJID` = `types.JID{User: "status", Server: "broadcast"}`

**20. `/api/link_group`** - Link group to community
- Request: `{ "parent_jid": "community@g.us", "child_jid": "group@g.us" }`
- Response: BasicResponse
- whatsmeow: `client.LinkGroup(ctx, parentJID, childJID)` (group.go)

**21. `/api/unlink_group`** - Unlink group from community
- Request: `{ "parent_jid": "community@g.us", "child_jid": "group@g.us" }`
- Response: BasicResponse
- whatsmeow: `client.UnlinkGroup(ctx, parentJID, childJID)` (group.go)

**22. `/api/get_sub_groups`** - Get community sub-groups
- Request: `{ "jid": "community@g.us" }`
- Response: `{ "success": true, "groups": [{"jid": "...", "name": "..."}] }`
- whatsmeow: `client.GetSubGroups(ctx, communityJID)` (group.go:548) -> `[]*types.GroupLinkTarget`

---

## Faza 2: Python MCP Server - Toate Functiile si Tool-urile Noi

### WP-PY-1: Bug fixes in whatsapp.py
- Sterge print cosmetic cu file:// din download_media (linia ~801-802)

### WP-PY-2: HTTP API wrappers in whatsapp.py (18 functii noi)
Fiecare endpoint Go din Faza 1 primeste o functie wrapper. Grupate dupa categorie.

**Functii noi de adaugat dupa `get_contact_groups` (~linia 534):**

```python
# --- Group Info & Management ---
def get_group_info(jid: str) -> Dict[str, Any]: ...
def get_group_invite_link(jid: str, reset: bool = False) -> Tuple[bool, str, str]: ...
def set_group_topic(jid: str, topic: str) -> Tuple[bool, str]: ...
def set_group_announce(jid: str, announce: bool) -> Tuple[bool, str]: ...
def set_group_locked(jid: str, locked: bool) -> Tuple[bool, str]: ...
def set_group_join_approval(jid: str, mode: bool) -> Tuple[bool, str]: ...
def is_on_whatsapp(phones: List[str]) -> List[Dict[str, Any]]: ...

# --- Message Operations ---
def send_reaction(chat_jid: str, sender_jid: str, message_id: str, reaction: str) -> Tuple[bool, str]: ...
def edit_message(chat_jid: str, message_id: str, new_text: str) -> Tuple[bool, str]: ...
def delete_message(chat_jid: str, sender_jid: str, message_id: str) -> Tuple[bool, str]: ...
def mark_read(chat_jid: str, sender_jid: str, message_ids: List[str]) -> Tuple[bool, str]: ...
def create_poll(chat_jid: str, question: str, options: List[str], max_selections: int = 1) -> Tuple[bool, str]: ...
def send_reply(chat_jid: str, quoted_message_id: str, quoted_sender_jid: str, message: str, quoted_content: str = "") -> Tuple[bool, str]: ...

# --- Advanced ---
def send_presence(presence: str) -> Tuple[bool, str]: ...
def set_status_message(message: str) -> Tuple[bool, str]: ...
def create_newsletter(name: str, description: str = "") -> Dict[str, Any]: ...
def get_newsletters() -> List[Dict[str, Any]]: ...
def newsletter_send(jid: str, message: str) -> Tuple[bool, str]: ...
def send_status(message: str) -> Tuple[bool, str]: ...

# --- Community ---
def link_group(parent_jid: str, child_jid: str) -> Tuple[bool, str]: ...
def unlink_group(parent_jid: str, child_jid: str) -> Tuple[bool, str]: ...
def get_sub_groups(jid: str) -> List[Dict[str, Any]]: ...
```

### WP-PY-3: SQL Analytics + Pure Python tools in whatsapp.py (6 functii noi)

**Acestea NU necesita Go bridge - sunt direct pe SQLite:**

```python
def get_group_activity_report(chat_jid: str, days: int = 30) -> Dict[str, Any]:
    """Message count, unique senders, messages/day for a group over N days."""
    # SQL: SELECT COUNT(*), COUNT(DISTINCT sender), ... FROM messages
    # WHERE chat_jid = ? AND timestamp > datetime('now', '-N days')

def get_member_engagement(chat_jid: str, days: int = 30) -> List[Dict[str, Any]]:
    """Per-member stats: message count, last active, classification."""
    # SQL: SELECT sender, COUNT(*), MAX(timestamp) FROM messages
    # WHERE chat_jid = ? AND timestamp > ... GROUP BY sender

def cross_group_search(query: str, chat_jid_pattern: Optional[str] = None, limit: int = 50) -> List[Dict[str, Any]]:
    """Search messages across all groups or groups matching pattern."""
    # SQL: SELECT ... FROM messages JOIN chats WHERE content LIKE ?
    # AND (chat_jid LIKE ? OR ? IS NULL) LIMIT ?

def get_participant_journey(jid: str) -> List[Dict[str, Any]]:
    """All groups + activity timeline for a contact."""
    # Combines get_contact_groups() result with SQL message stats per group

def broadcast_to_groups(group_jids: List[str], message: str) -> List[Dict[str, Any]]:
    """Send same message to multiple groups with 3s delay between sends."""
    # Loops over send_message() with time.sleep(3) between calls
    # Returns list of {jid, success, message} for each group

def get_group_overlap(group_jids: List[str]) -> Dict[str, Any]:
    """Compare members across 2+ groups - who's in all, who's unique."""
    # Calls get_group_info() for each group, compares participant sets
    # Returns: {common: [...], unique_per_group: {jid: [...]}}
```

### WP-PY-4: MCP tool definitions in main.py (22 tools noi)

**Import-uri noi de adaugat:**
```python
from whatsapp import (
    # ... existing imports ...
    get_group_info as whatsapp_get_group_info,
    get_group_invite_link as whatsapp_get_group_invite_link,
    set_group_topic as whatsapp_set_group_topic,
    set_group_announce as whatsapp_set_group_announce,
    set_group_locked as whatsapp_set_group_locked,
    set_group_join_approval as whatsapp_set_group_join_approval,
    is_on_whatsapp as whatsapp_is_on_whatsapp,
    send_reaction as whatsapp_send_reaction,
    edit_message as whatsapp_edit_message,
    delete_message as whatsapp_delete_message,
    mark_read as whatsapp_mark_read,
    create_poll as whatsapp_create_poll,
    send_reply as whatsapp_send_reply,
    send_presence as whatsapp_send_presence,
    set_status_message as whatsapp_set_status_message,
    create_newsletter as whatsapp_create_newsletter,
    get_newsletters as whatsapp_get_newsletters,
    newsletter_send as whatsapp_newsletter_send,
    get_group_activity_report as whatsapp_get_group_activity_report,
    get_member_engagement as whatsapp_get_member_engagement,
    cross_group_search as whatsapp_cross_group_search,
    get_participant_journey as whatsapp_get_participant_journey,
)
```

**22 MCP tool-uri noi** - fiecare cu docstring clar, Args documentate, return type Dict[str, Any].

---

## Faza 3: Build & Verification

### Step 1: Go build
```bash
cd whatsapp-bridge && go build -o whatsapp-bridge main.go
```
- Daca esueaza: fix compile errors, nu continua

### Step 2: Python syntax check
```bash
cd whatsapp-mcp-server && uv run python -c "import main; print('OK')"
```

### Step 3: Bridge restart (facut de agent)
```bash
# Kill existing
pkill -f whatsapp-bridge
# Start new
cd whatsapp-bridge && ./whatsapp-bridge -storage-path="$(pwd)/store" &
sleep 3
# Test all new endpoints respond
curl -s -X POST http://localhost:8080/api/get_group_info -H "Content-Type: application/json" -d '{"jid":"test@g.us"}' | head -1
curl -s -X POST http://localhost:8080/api/send_reaction -H "Content-Type: application/json" -d '{"chat_jid":"test","sender_jid":"test","message_id":"test","reaction":"🔥"}' | head -1
# ... etc pentru fiecare endpoint
```

### Step 4: MCP server restart (facut de USER)
User trebuie sa restarteze Claude Desktop/MCP client pentru a reincarca tool-urile.

---

## Team Execution Strategy

### Agent Assignments

**Agent 1 "go-bridge"** (general-purpose, bypassPermissions):
- Citeste: main.go complet
- Executa: BF-2 (DB indexes) + WP-GO-1 + WP-GO-2 + WP-GO-3
- Adauga TOATE structurile, functiile si handler-ele noi
- La final: `go build` pentru verificare
- **IMPORTANT**: Adauga `"crypto/rand"` la imports (necesar pentru poll encKey)

**Agent 2 "python-mcp"** (general-purpose, bypassPermissions):
- Citeste: whatsapp.py si main.py complet
- Executa: BF-1 (cosmetic print) + WP-PY-1 + WP-PY-2 + WP-PY-3 + WP-PY-4
- Adauga TOATE functiile wrapper, SQL analytics, si MCP tool definitions
- La final: `uv run python -c "import main"` pentru verificare

**Agent 3 "code-review"** (Explore):
- Se lanseaza DUPA ce agentii 1 si 2 termina
- Citeste main.go, whatsapp.py, main.py
- Verifica: patterns respectate, imports corecte, endpoint paths match intre Go si Python, toate functiile au MCP tools corespunzatoare, nu sunt typos

**Leader (tu)**:
- Coordoneaza agentii 1 si 2 in paralel
- Dupa ce termina: lanseaza agent 3 pentru code review
- Dupa review: go build + restart bridge
- Cere user-ului sa restarteze MCP

### Ordinea de executie:
```
[Agent 1: Go bridge] ──────────┐
                                ├──> [Agent 3: Code Review] ──> [Build + Restart]
[Agent 2: Python MCP] ─────────┘
```

Agentii 1 si 2 lucreaza **IN PARALEL** (fisiere diferite).

---

## API Contract Summary (Go endpoint -> Python function -> MCP tool)

| # | Go Endpoint | Python Function | MCP Tool Name | Category |
|---|------------|----------------|--------------|----------|
| 1 | `/api/get_group_info` | `get_group_info()` | `get_group_info` | Group |
| 2 | `/api/get_group_invite_link` | `get_group_invite_link()` | `get_group_invite_link` | Group |
| 3 | `/api/set_group_topic` | `set_group_topic()` | `set_group_topic` | Group |
| 4 | `/api/set_group_announce` | `set_group_announce()` | `set_group_announce` | Group |
| 5 | `/api/set_group_locked` | `set_group_locked()` | `set_group_locked` | Group |
| 6 | `/api/set_group_join_approval` | `set_group_join_approval()` | `set_group_join_approval` | Group |
| 7 | `/api/is_on_whatsapp` | `is_on_whatsapp()` | `is_on_whatsapp` | User |
| 8 | `/api/send_reaction` | `send_reaction()` | `send_reaction` | Message |
| 9 | `/api/edit_message` | `edit_message()` | `edit_message` | Message |
| 10 | `/api/delete_message` | `delete_message()` | `delete_message` | Message |
| 11 | `/api/mark_read` | `mark_read()` | `mark_read` | Message |
| 12 | `/api/create_poll` | `create_poll()` | `create_poll` | Message |
| 13 | `/api/send_reply` | `send_reply()` | `send_reply` | Message |
| 14 | `/api/send_presence` | `send_presence()` | `send_presence` | Presence |
| 15 | `/api/set_status_message` | `set_status_message()` | `set_status_message` | User |
| 16 | `/api/create_newsletter` | `create_newsletter()` | `create_newsletter` | Newsletter |
| 17 | `/api/get_newsletters` | `get_newsletters()` | `get_newsletters` | Newsletter |
| 18 | `/api/newsletter_send` | `newsletter_send()` | `newsletter_send` | Newsletter |
| 19 | N/A (SQL) | `get_group_activity_report()` | `get_group_activity_report` | Analytics |
| 20 | N/A (SQL) | `get_member_engagement()` | `get_member_engagement` | Analytics |
| 21 | N/A (SQL) | `cross_group_search()` | `cross_group_search` | Analytics |
| 22 | N/A (SQL) | `get_participant_journey()` | `get_participant_journey` | Analytics |
| 23 | N/A (Python) | `broadcast_to_groups()` | `broadcast_to_groups` | Orchestration |
| 24 | N/A (Python) | `get_group_overlap()` | `get_group_overlap` | Analytics |
| 25 | `/api/send_status` | `send_status()` | `send_status` | Status |
| 26 | `/api/link_group` | `link_group()` | `link_group` | Community |
| 27 | `/api/unlink_group` | `unlink_group()` | `unlink_group` | Community |
| 28 | `/api/get_sub_groups` | `get_sub_groups()` | `get_sub_groups` | Community |

---

## Commit Strategy

Un singur commit la final cu toate schimbarile:
```
Add 28 new MCP tools + fix bugs for coaching platform

New tools:
- Group: get_group_info, get_group_invite_link, set_group_topic,
  set_group_announce, set_group_locked, set_group_join_approval
- User: is_on_whatsapp, set_status_message, send_presence
- Message: send_reaction, edit_message, delete_message, mark_read,
  create_poll, send_reply
- Newsletter: create_newsletter, get_newsletters, newsletter_send
- Status: send_status
- Community: link_group, unlink_group, get_sub_groups
- Analytics (SQL): get_group_activity_report, get_member_engagement,
  cross_group_search, get_participant_journey
- Orchestration (Python): broadcast_to_groups, get_group_overlap

Bug fixes: add DB indexes, remove cosmetic file:// print
```
