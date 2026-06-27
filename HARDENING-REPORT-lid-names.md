# Hardening report - fix @lid chat-name corruption at the SOURCE (Go bridge)

**Data:** 2026-06-27
**Scope:** WRITE-side root cause în `whatsapp-bridge/main.go` (`GetChatName`). Python read-side
(`whatsapp-mcp-server/`) **nu** a fost atins (era deja reparat).
**Status deploy:** 🟢 **DEPLOYAT** (2026-06-27 ~13:11, după confirmarea „Go" a lui Cristi). Binarul a
fost rebuild-uit, backfill-ul aplicat (50 rânduri), bridge-ul repornit. **Atenție:** deploy-ul a scos
la iveală o problemă macOS independentă de cod - binarul nu mai poate fi pornit de launchd din
`~/Downloads` după rebuild; a fost **mutat în `~/CLAUDE/whatsapp-bridge/`** și plist-ul actualizat
(vezi §6). Verificarea finală în §8.

---

## 1. Cauza (verificată pe DB-ul live, read-only)

La un chat **nou** `@lid` fără nume de contact stocat, vechiul `GetChatName` făcea
`name = sender`. `sender = msg.Info.Sender.User` (main.go:1311). Pentru un mesaj **OUTGOING**
(owner-ul scrie primul într-un chat nou), `sender` este **LID-ul propriu al owner-ului**, deci
`StoreChat` scria numărul owner-ului ca nume al **celuilalt** participant. Pentru mesaje
**INCOMING** scria LID-ul propriu al contactului. În ambele cazuri `chats.name` devenea un număr.

Confirmare pe `messages.db` (read-only):

- `own_jid` (API `/api/status`) = `40720900690@s.whatsapp.net`, mapat în `jid_mappings` la
  `169440771625138@lid` (LID-ul owner-ului).
- **28** de chat-uri `@lid` au `name = "169440771625138"` (exact LID-ul owner-ului) → varianta OUTGOING a bug-ului.
- Restul chat-urilor `@lid` cu nume pur-numeric au ca `name` propriul LID al contactului → varianta INCOMING.
- Numele real există de regulă pe rândul PN, accesibil prin `jid_mappings` (`lid_jid → pn_jid`).
  Ex.: `653019619414@lid` (name corupt `653019619414`) → `40743297575@s.whatsapp.net` = **"Raluca Culda"**.
- **50** de chat-uri `@lid` pur-numerice sunt rezolvabile la un nume PN real (candidați de backfill);
  alte **36** nu au încă un nume real mapat (rămân neatinse de backfill-ul principal).

---

## 2. Fix-ul - diff exact (`whatsapp-bridge/main.go`)

### 2a. Helper nou `isRealName` (+ import `unicode`)

```diff
@@ import (
 	"strings"
 	"syscall"
 	"time"
+	"unicode"
@@ după backfillLIDMappings(...)
+// isRealName reports whether s looks like a human-readable name rather than a
+// bare identifier (a LID or a phone number). It requires at least one letter,
+// which rejects all-numeric "names" such as "169440771625138" or "40720900690".
+func isRealName(s string) bool {
+	for _, r := range s {
+		if unicode.IsLetter(r) {
+			return true
+		}
+	}
+	return false
+}
```

### 2b. Ramura individual-contact din `GetChatName` (before → after)

```diff
 		// This is an individual contact
 		logger.Infof("Getting name for contact: %s", chatJID)

-		// Just use contact info (full name)
+		// Prefer the contact's real full name from whatsmeow's contact store.
 		contact, err := client.Store.Contacts.GetContact(context.Background(), jid)
-		if err == nil && contact.FullName != "" {
+		if err == nil && isRealName(contact.FullName) {
 			name = contact.FullName
-		} else if sender != "" {
-			// Fallback to sender
-			name = sender
-		} else {
-			// Last fallback to JID
+		} else if jid.Server == types.HiddenUserServer {
+			// New @lid contact with no stored name. Resolve LID -> PN via the
+			// jid_mappings table and reuse the real name already on the PN chat
+			// row. We must NEVER fall back to the message `sender` here: for an
+			// OUTGOING message `sender` is the OWNER's own LID, so doing so would
+			// overwrite the other party's chat name with our own number -- this
+			// is the @lid chat-name corruption bug this branch fixes.
+			var pnJID string
+			if e := messageStore.db.QueryRow(
+				"SELECT pn_jid FROM jid_mappings WHERE lid_jid = ?", chatJID,
+			).Scan(&pnJID); e == nil && pnJID != "" {
+				var pnName string
+				if e := messageStore.db.QueryRow(
+					"SELECT name FROM chats WHERE jid = ?", pnJID,
+				).Scan(&pnName); e == nil && isRealName(pnName) {
+					name = pnName
+				} else if pn, e := types.ParseJID(pnJID); e == nil && pn.User != "" {
+					// No real name yet, but the phone number beats a bare LID.
+					name = pn.User
+				}
+			}
+		}
+
+		// Absolute last resort: the chat's own JID user part (the phone number
+		// for a PN chat, the LID for an unresolved @lid chat). Never the sender.
+		if name == "" {
 			name = jid.User
 		}

 		logger.Infof("Using contact name: %s", name)
```

---

## 3. De ce repară cauza

1. **`sender` nu mai e folosit niciodată ca nume.** Asta elimină exact mecanismul prin care
   LID-ul owner-ului (outgoing) sau LID-ul propriu al contactului (incoming) ajungeau în
   `chats.name`. `sender` rămâne parametru al funcției (folosit de semnătură/apelanți), dar nu mai
   influențează numele - în Go parametrii nefolosiți sunt permiși, deci semnătura și cele 2 call-site-uri
   rămân neatinse.
2. **`isRealName` respinge nume pur-numerice** atât pentru `contact.FullName` cât și pentru numele PN,
   deci un LID/număr nu mai e acceptat ca "nume" din greșeală.
3. **Rezolvare LID → PN → nume real** prin `jid_mappings` (deja populat de bridge): pentru un chat
   `@lid` nou se ia numele real de pe rândul PN corespunzător (ex. „Raluca Culda"). Reutilizează
   handle-ul `messageStore.db` existent - fără conexiune nouă, fără refactor.
4. **Degradare sigură:** dacă nu există nume real, preferă **numărul de telefon** (din `pn_jid`) în
   locul unui LID; abia ca ultimă instanță cade pe `jid.User` (LID-ul propriu al chat-ului), niciodată pe owner.
5. **Acoperă și varianta PN a bug-ului:** pentru un chat PN nou unde owner-ul scrie primul, vechiul cod
   punea `name = sender` = numărul owner-ului; acum, fiindcă `jid.Server != HiddenUserServer`, se cade
   direct pe `jid.User` = numărul corect al celuilalt participant.

Gardul `jid.Server == types.HiddenUserServer` (constanta whatsmeow pentru `"lid"`, folosită deja la
main.go:1286/1298) limitează interogarea `jid_mappings` strict la chat-urile `@lid`.

---

## 4. Compilare (binarul live NEATINS)

```bash
cd whatsapp-bridge && go build -o /tmp/whatsapp-bridge-test main.go
```

- **Rezultat:** ✅ **BUILD OK** (`/tmp/whatsapp-bridge-test`, 29 MB).
- `gofmt`: adăugirile mele sunt curate. (`gofmt -l` semnalează `main.go` doar pentru o aliniere de
  struct **preexistentă** la liniile ~1468/1484, complet în afara modificărilor mele - nu am atins-o,
  ca să nu introduc churn nelegat.)
- Binarul live `whatsapp-bridge/whatsapp-bridge` (datat Jun 19) **nu** a fost suprascris. Build-ul a
  mers doar în `/tmp`.

---

## 5. Backfill pentru rândurile deja corupte

Fișier: **`whatsapp-bridge/backfill_chat_names.sql`** (creat - **NU a fost executat**).
Conține: (1) preview read-only, (2) UPDATE în tranzacție, (3) verificare, (4) un UPDATE opțional
comentat care upgradează LID-urile rămase la numărul de telefon.

### Preview (rulat read-only pe DB-ul live ca dry-run → **50 rânduri**)

```sql
SELECT c.jid AS lid_jid, c.name AS current_corrupt_name,
       m.pn_jid AS mapped_pn_jid, p.name AS new_name
FROM chats c
JOIN jid_mappings m ON m.lid_jid = c.jid
JOIN chats        p ON p.jid    = m.pn_jid
WHERE c.jid LIKE '%@lid'
  AND c.name NOT GLOB '*[A-Za-z]*'      -- numele curent e pur-numeric
  AND p.name      GLOB '*[A-Za-z]*'     -- rândul PR mapat are nume real
ORDER BY c.name = '169440771625138' DESC, p.name;
```

Exemple din preview (cele corupte cu LID-ul owner-ului apar primele):

| lid_jid | current_corrupt_name | mapped_pn_jid | new_name |
|---|---|---|---|
| 144414097813624@lid | 169440771625138 | 40726313216@s.whatsapp.net | Amalia Arhire |
| 124047362941061@lid | 169440771625138 | 40761122495@s.whatsapp.net | Ana Vochiță |
| 653019619414@lid | 653019619414 | 40743297575@s.whatsapp.net | Raluca Culda |

### UPDATE (formă portabilă cu subquery corelat - **NU executat**)

```sql
BEGIN TRANSACTION;
UPDATE chats
SET name = (
    SELECT p.name FROM jid_mappings m JOIN chats p ON p.jid = m.pn_jid
    WHERE m.lid_jid = chats.jid AND p.name GLOB '*[A-Za-z]*'
)
WHERE chats.jid LIKE '%@lid'
  AND chats.name NOT GLOB '*[A-Za-z]*'
  AND EXISTS (
      SELECT 1 FROM jid_mappings m JOIN chats p ON p.jid = m.pn_jid
      WHERE m.lid_jid = chats.jid AND p.name GLOB '*[A-Za-z]*'
  );
COMMIT;
```

Verificarea de la final trebuie să raporteze `0` rânduri corupte-dar-rezolvabile rămase.

---

## 6. Deploy - 🟢 EXECUTAT (cu o complicație macOS rezolvată)

### 6a. Ce s-a rulat efectiv (în ordine)

```bash
# 0) Backup DB  →  /Users/cristi/CLAUDE/whatsapp-media/messages.db.bak-20260627-125745
# 1) launchctl bootout gui/$(id -u)/com.kilostop.whatsapp-bridge          # oprit bridge-ul (era PID 701)
# 2) cd whatsapp-bridge && go build -o whatsapp-bridge main.go            # rebuild în repo (sha256 498ffdd…)
# 3) sqlite3 messages.db < backfill_chat_names.sql                        # 50 rânduri UPDATE-uite, verify=0
# 4) launchctl bootstrap … com.kilostop.whatsapp-bridge.plist            # repornit
```

### 6b. ⚠️ Complicație macOS descoperită la restart (root cause găsit cu `sample`)

După rebuild, bridge-ul pornit de launchd **se bloca la startup** (proces viu, dar fără `:8080`, fără
stdout, fără socket-uri). `sample <pid>` a arătat procesul blocat în **`dyld` → `__open`** la maparea
**propriului binar de pe disc** - nici nu ajungea la `main()`. Cauza: binarul rula din **`~/Downloads`**,
folder protejat de **TCC/Gatekeeper**. După rebuild, binarul are un **cdhash nou + xattr
`com.apple.provenance`** (neșters de `xattr -c`, e protejat de SIP), deci macOS cere o re-evaluare la
prima execuție; un **LaunchAgent nu are sesiune GUI** ca să dea consimțământul → `open()` atârnă la
nesfârșit. Binarul **vechi** mergea fiindcă cdhash-ul lui fusese deja aprobat cândva; în **foreground**
merge fiindcă sesiunea terminalului moștenește accesul la Downloads.

**Dovadă definitivă:** exact același binar copiat într-un folder NEprotejat și pornit de launchd a urcat
în **4 secunde**.

### 6c. Fix aplicat: binarul de runtime mutat în afara `~/Downloads`

```bash
# binarul instalat într-o locație neprotejată (sha256 identic cu cel din repo)
/Users/cristi/CLAUDE/whatsapp-bridge/whatsapp-bridge
# plist actualizat (ProgramArguments[0] + WorkingDirectory), backup:
~/Library/LaunchAgents/com.kilostop.whatsapp-bridge.plist.bak-20260627-131029
```

Bridge-ul rulează acum din `~/CLAUDE/whatsapp-bridge/` → **UP în ~4s, PID nou, `connected:true`**.
Sursa și binarul rebuild-uit rămân și în repo (`whatsapp-bridge/whatsapp-bridge`) pentru build-uri
manuale; doar **launchd** pointează la copia instalată.

### 6d. ‼️ Workflow nou pentru rebuild-uri viitoare

Fiindcă launchd nu mai pornește binarul din `~/Downloads`, după orice `go build` trebuie copiat:

```bash
cd /Users/cristi/Downloads/CODING/whatsapp-mcp/whatsapp-bridge
go build -o whatsapp-bridge main.go
launchctl bootout gui/$(id -u)/com.kilostop.whatsapp-bridge
cp whatsapp-bridge /Users/cristi/CLAUDE/whatsapp-bridge/whatsapp-bridge   # ← pasul nou esențial
launchctl bootstrap gui/$(id -u) ~/Library/LaunchAgents/com.kilostop.whatsapp-bridge.plist
```

**Alternativă** dacă preferi binarul în repo (`~/Downloads`): acordă-i manual **Full Disk Access** în
System Settings → Privacy & Security (per-binar, fragil la fiecare rebuild) - nu recomand; mutarea e mai curată.

---

## 7. Ce am atins (toate executate, cu confirmarea „Go")

- `whatsapp-bridge/main.go` - `isRealName` + ramura individual din `GetChatName` + import `unicode`
  (working copy, **necomis** - git neatins, cum ai cerut).
- `whatsapp-bridge/backfill_chat_names.sql` - nou; **rulat** pe DB (50 rânduri).
- `messages.db` - **50 nume corectate** (backup la `…bak-20260627-125745`).
- Binar rebuild-uit + **mutat** în `~/CLAUDE/whatsapp-bridge/`; plist actualizat (backup salvat).
- Bridge **repornit** din locația nouă, sănătos.
- `whatsapp-mcp-server/` (Python) - **neatins**.

---

## 8. Verificare finală (live)

| Check | Rezultat |
|---|---|
| `/api/status` | `{"connected":true,"logged_in":true,"own_jid":"40720900690@s.whatsapp.net"}` |
| launchd service | `state=running`, `runs=1`, `program=/Users/cristi/CLAUDE/whatsapp-bridge/whatsapp-bridge` |
| Timp până la `:8080` | ~4s |
| Backfill | 50 UPDATE-uri, `remaining_corrupt_resolvable = 0` |
| Spot-check DB | `653019619414@lid`→Raluca Culda, `51827387179256@lid`→Ana Sipciu, `124047362941061@lid`→Ana Vochiță, `144414097813624@lid`→Amalia Arhire |
| Fix live (run manual) | log: `Using existing chat name for 51827387179256@lid: Ana Sipciu` (înainte: `169440771625138`) |

> Notă TZ: log-ul Go scrie cu **+1h** față de shell (ex. `13:57:45 Disconnecting` în log = `12:57:45`
> shell = momentul bootout-ului). Liniile vechi cu `169440771625138` din log sunt **istorice**, dinainte
> de deploy - DB-ul corectat e sursa de adevăr.
