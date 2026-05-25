# WhatsApp LID Migration Guide

Ghid pentru colegii care au deja repo-ul whatsapp-mcp si trebuie sa treaca pe versiunea LID-safe.

## Ce s-a schimbat

WhatsApp migreaza de la JID-uri bazate pe telefon (`40720666029@s.whatsapp.net`) la **Linked ID** (`51827387179256@lid`). Bridge-ul Go primea deja mesajele, dar le stoca sub LID-ul nou. Python MCP server le cauta sub JID-ul vechi si nu le gasea - ceea ce activa fallback-ul catre ChatStorage.sqlite, care uneori se bloca.

**Versiunea noua rezolva asta:**

- Bridge-ul Go creeaza un tabel `jid_mappings` in `messages.db` cu perechi LID-PN
- La pornire, face backfill automat din whatsmeow Store.LIDs (populat de WhatsApp)
- Python MCP server rezolva transparent ambele JID-uri la query
- ChatStorage fallback ruleaza acum in subprocess cu timeout de 3 secunde (nu mai poate bloca)

## Pasi dupa `git pull`

### 1. Pull ultima versiune

```bash
cd ~/Downloads/CODING/whatsapp-mcp   # sau unde aveti repo-ul
git pull
```

### 2. Rebuild bridge-ul Go

```bash
cd whatsapp-bridge
go build -o whatsapp-bridge .
```

Verificati ca build-ul trece fara erori. Daca lipsesc dependinte:

```bash
go mod tidy
go build -o whatsapp-bridge .
```

### 3. Restart bridge

Opriti bridge-ul vechi:

```bash
# Gasiti PID-ul
ps aux | grep whatsapp-bridge | grep -v grep

# Opriti-l
kill <PID>
```

Porniti noul bridge:

```bash
cd whatsapp-bridge
./whatsapp-bridge -storage-path /Users/$USER/CLAUDE/whatsapp-media
```

Sau cu nohup daca rulati in background:

```bash
nohup ./whatsapp-bridge -storage-path /Users/$USER/CLAUDE/whatsapp-media > /tmp/whatsapp-bridge.log 2>&1 &
```

**Important:** Nu trebuie sa faceti re-pairing QR. Sesiunea se pastreaza.

### 4. Verificati backfill-ul

Dupa ~15 secunde de la pornire, verificati ca mapping-urile s-au creat:

```bash
sqlite3 /Users/$USER/CLAUDE/whatsapp-media/messages.db "SELECT COUNT(*) FROM jid_mappings;"
```

Ar trebui sa vedeti un numar > 0. Daca vedeti eroarea `no such table: jid_mappings`, bridge-ul nu a pornit cu binarul nou.

Pentru a vedea mapping-urile:

```bash
sqlite3 /Users/$USER/CLAUDE/whatsapp-media/messages.db "SELECT lid_jid, pn_jid FROM jid_mappings LIMIT 10;"
```

### 5. Verificati ca MCP server-ul functioneaza

```bash
# Status bridge
mcpl call --no-daemon whatsapp connection '{"action":"status"}'

# Mesaje de la un contact (folositi numarul vechi - ar trebui sa gaseasca si mesajele LID)
mcpl call --no-daemon whatsapp list_messages '{"chat_jid":"40720666029@s.whatsapp.net","limit":3,"include_context":false}'

# Lista chat-uri (LID chats ar trebui sa arate cu nume umane, nu numere)
mcpl call --no-daemon whatsapp list_chats '{"limit":5}'
```

### 6. Restart MCPL daemon (optional)

Daca folositi mcpl cu daemon (fara `--no-daemon`), restartati daemon-ul ca sa preia noul whatsapp-mcp-server:

```bash
mcpl session stop
# La urmatorul mcpl call, daemon-ul porneste automat
```

## Ce se intampla automat

- **La fiecare mesaj primit**, bridge-ul extrage mapping-uri LID-PN din campurile `SenderAlt` si `RecipientAlt` ale evenimentului WhatsApp
- **La pornirea bridge-ului**, face un scan complet al chat-urilor `@lid` existente si le rezolva prin `Store.LIDs.GetPNForLID()`
- **Python MCP server** rezolva JID-uri transparent - cine cauta `40720666029@s.whatsapp.net` primeste si mesajele din `51827387179256@lid`
- **list_chats** deduplica automat chat-urile care au si PN si LID

## Troubleshooting

**Bridge-ul nu porneste / crash la startup:**

Verificati ca aveti Go 1.25+ si ca dependintele sunt la zi:

```bash
go version       # trebuie >= 1.25
go mod tidy      # actualizeaza dependinte
go build -o whatsapp-bridge .
```

**`jid_mappings` e gol dupa restart:**

Backfill-ul asteapta 10 secunde dupa conectare (ca whatsmeow sa faca history sync). Verificati log-ul:

```bash
grep "Backfill" /tmp/whatsapp-bridge.log
```

Daca vedeti "found 0 LID chats to resolve", bridge-ul nu are inca chat-uri LID in `messages.db`. Acestea apar pe masura ce primiti mesaje de la contacte migrate.

**Mesajele unui contact nu apar dupa migrare:**

Contactul nu a trimis inca un mesaj dupa restart. Mapping-ul se creeaza la primul mesaj primit de la acel contact, sau la backfill daca chat-ul LID exista deja in DB.

**ChatStorage timeout (mesaj "ChatStorage fallback timed out"):**

E normal si nu afecteaza functionarea. Inseamna ca WhatsApp Desktop era ocupat (WAL checkpoint). Mesajele principale se citesc din `messages.db`, ChatStorage e doar backup.

## Schema noua in messages.db

```sql
-- Tabel nou (creat automat de bridge)
CREATE TABLE jid_mappings (
    lid_jid TEXT PRIMARY KEY,       -- ex: 51827387179256@lid
    pn_jid TEXT NOT NULL UNIQUE,    -- ex: 40720666029@s.whatsapp.net
    source TEXT DEFAULT 'event',    -- event_alt / store_lids / backfill
    updated_at TEXT
);
```

Tabelele existente (`messages`, `chats`) nu sunt modificate.
