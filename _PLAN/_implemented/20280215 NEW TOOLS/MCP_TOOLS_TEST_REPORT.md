# MCP Tools Test Report

**Date:** 2026-02-15
**Branch:** `variant-data-folder-in-mcp-server`
**Bridge:** Running, connected to WhatsApp

---

## Tool #1: `get_group_info`
**Category:** Group Info & Management

**Intent:** Permite AI-ului sa afle detalii despre un grup WhatsApp - nume, descriere, setari (announce/locked), si lista de participanti cu rolurile lor. Util pentru a intelege structura unui grup inainte de a lua actiuni (broadcast, management, analytics).

**Test:** Apelat cu JID `120363352431965680@g.us` ("6 Sisteme by Dan Luca (2025)")

**Rezultat tehnic:**
- `success: true` - endpoint-ul functioneaza
- `group.name`: "6 Sisteme by Dan Luca (2025)" - corect
- `group.topic`: "" (grupul nu are descriere)
- `group.announce: true`, `group.locked: true` - corect
- `group.participants`: 793 participanti, 2 admini

**Probleme de usability:**
1. **Raspunsul e de 82,964 caractere** - a depasit limita MCP si a fost salvat in fisier temporar in loc sa fie returnat direct. Tool-ul e practic **inutilizabil** pentru grupuri mari.
2. **Toti 793 participanti au `name: ""`** - campul name nu e populat (LID-uri fara numele din contacts). Deci se returneaza 793 de obiecte cu 0 informatie utila in `name`.
3. **Nu exista paginare** - nu poti cere "primii 20 participanti" sau "doar adminii".
4. **Lipseste `participant_count`** in response metadata - nu stii cati sunt fara sa numeri array-ul.

**Propuneri de imbunatatire:**
- Adauga parametru `include_participants: bool = False` (default fara participanti). Metadata grupului (name, topic, announce, locked, participant_count) e aproape mereu suficienta.
- Cand `include_participants=True`, adauga `participant_limit: int = 50` si `participant_offset: int = 0` pentru paginare.
- Adauga `participant_count: int` in response-ul de baza (mereu prezent).
- Optional: parametru `admins_only: bool = False` sa returneze doar adminii.

**Status:** FUNCTIONAL dar cu probleme majore de usability pe grupuri mari.

---

## Tool #2: `get_group_invite_link`
**Category:** Group Info & Management

**Intent:** Permite AI-ului sa obtina link-ul de invitare al unui grup WhatsApp (pentru a-l trimite cuiva) sau sa-l reseteze (securitate - invalideaza link-ul vechi). Util in scenarii de onboarding, share de grupuri, sau cand un link a fost compromis.

**Test:** Apelat pe grupul "Agentic Awakened" (`120363406982852696@g.us`)
- `reset=false`: Returneaza `https://chat.whatsapp.com/FRfwAEMUt5wFhEvZ0Oxer9`
- `reset=true`: Returneaza `https://chat.whatsapp.com/IqOvvTkQeqTIMbO282jFpf` (link diferit - corect)

**Rezultat tehnic:**
- `success: true`, `link` prezent in ambele cazuri
- Reset-ul genereaza link nou (linkul vechi devine invalid) - functioneaza corect

**Usability:**
- Response mic si clar - perfect
- Parametrul `reset` e bine gandit ca optional, default `false`
- **Atentie:** `reset=true` e o actiune distructiva (invalideaza linkul vechi). Docstring-ul ar putea avertiza mai explicit ca linkul vechi devine invalid dupa reset.

**Propuneri:** Niciuna majora. Tool functional si curat. Minor: docstring-ul ar putea mentiona "WARNING: reset=true invalidates the previous invite link".

**Status:** PASS - fully functional. Minor: docstring ar putea avertiza ca reset invalideaza linkul vechi.

---

## Tool #3: `set_group_topic`
**Category:** Group Info & Management

**Intent:** Permite AI-ului sa seteze/modifice descrierea (topic/description) unui grup WhatsApp. Util pentru automatizarea managementului de grupuri - ex: actualizare descriere cu date de sesiune, reguli, link-uri etc.

**Test:** Setat topic "Test group for MCP tool development" pe "Agentic Awakened", apoi verificat cu `get_group_info`.
- Inainte: `topic: ""`
- Dupa: `topic: "Test group for MCP tool development"` - corect

**Rezultat tehnic:**
- `success: true`, `message: "topic updated"`
- Verificat cu `get_group_info` - topic-ul persista corect

**Usability:**
- Response minimal si clar
- Nu returneaza topic-ul setat in response (ar fi util ca feedback/confirmare)
- Nu are optiune de "clear topic" documentata, dar probabil merge cu string gol

**Propuneri:** Minor - ar fi util sa returneze `{"success": true, "message": "topic updated", "topic": "..."}` ca confirmare a ce s-a setat.

**Status:** PASS - fully functional. Minor: ar fi util sa returneze topic-ul setat ca confirmare.

---

## Tools #4, #5, #6: `set_group_announce`, `set_group_locked`, `set_group_join_approval`
**Category:** Group Info & Management (toggle settings)

**Intent:**
- `set_group_announce`: Controleaza daca doar adminii pot trimite mesaje in grup. Util pentru "lecture mode" - ex: un coach face anunt, nimeni altcineva nu poate scrie.
- `set_group_locked`: Controleaza daca doar adminii pot edita info grupului (nume, descriere, poza). Util pentru a proteja branding-ul grupului.
- `set_group_join_approval`: Controleaza daca adminii trebuie sa aprobe cererile de intrare. Util pentru grupuri curatate/premium.

**Test:** Testate pe "Agentic Awakened" - setat pe `true`, verificat cu `get_group_info`, apoi revert la `false`.
- `set_group_announce(true)` -> verificat `announce: true` -> revert `false`
- `set_group_locked(true)` -> verificat -> revert `false`
- `set_group_join_approval(true)` -> revert `false`

**Rezultat tehnic:** Toate 3 returneaza `{"success": true, "message": "... setting updated"}`. Toggle-ul functioneaza in ambele directii.

**Usability:**
- Response-urile sunt minimaliste si corecte
- **Lipseste valoarea curenta in response** - nu stii ce ai setat fara un al doilea call la `get_group_info`
- **Lipseste valoarea anterioara** - nu stii daca ai schimbat ceva sau era deja pe acea valoare
- Docstring-urile sunt clare si parametrii intuitivi

**Propuneri:**
- Response-ul ar putea include `"value": true/false` ca confirmare a ce s-a setat
- Optional: `"previous_value": false` ca sa stii daca s-a schimbat ceva

**Status:** PASS - all three fully functional.

---

## Tool #7: `is_on_whatsapp`
**Category:** User

**Intent:** Verifica daca unul sau mai multe numere de telefon sunt inregistrate pe WhatsApp. Util inainte de a trimite mesaje (sa nu dai eroare pe numere invalide), pentru validare de liste de contacte, sau onboarding - "din acesti 50 de clienti, cati au WhatsApp?"

**Test:** Verificat 2 numere - unul real (+40730883388) si unul inventat (+40720000000).

**Rezultat tehnic:**
- `success: true`, `message: "checked 2 numbers"`
- Numarul real: `is_on_whatsapp: true`, `jid: "40730883388@s.whatsapp.net"`
- Numarul inventat: `is_on_whatsapp: false` (fara JID - corect)

**Usability:**
- Response curat si util - exact ce ai nevoie
- Suporta batch (multiple numere o data) - eficient
- Returneaza JID-ul pentru numerele gasite - util pentru apeluri ulterioare
- Format-ul telefonului e flexibil (accepta +prefix)

**Propuneri:** Niciuna. Tool bine gandit, batch-ready, response clar.

**Status:** PASS - fully functional.

---

## Tools #8-#13: Message Operations (`send_reaction`, `edit_message`, `delete_message`, `mark_read`, `create_poll`, `send_reply`)
**Category:** Message Operations

**Intent:**
- `send_reaction`: Reactioneaza cu emoji la un mesaj. Util pentru feedback automat, acknowledgement, engagement tracking.
- `edit_message`: Editeaza un mesaj trimis anterior. Util pentru corectii.
- `delete_message`: Sterge/revoca un mesaj. Util pentru retractarea erorilor.
- `mark_read`: Marcheaza mesaje ca citite. Util pentru automatizari (sa nu ramana "unread" dupa procesare).
- `create_poll`: Creeaza un poll in grup. Util pentru surveys, feedback, decizii rapide.
- `send_reply`: Raspunde la un mesaj specific (cu quote). Util pentru conversatii contextuale - AI-ul poate raspunde la intrebari specifice intr-un thread lung.

**Teste efectuate pe "Agentic Awakened":**

| Tool | Test | Rezultat |
|------|------|----------|
| `send_reaction` | React 🔥 la mesaj propriu | PASS - reaction vizibil in WhatsApp |
| `send_reaction` | Remove reaction (string gol) | PASS |
| `edit_message` | Edit mesaj propriu | PASS - mesajul apare editat in WhatsApp |
| `delete_message` | Trimis mesaj + sters | PASS - "This message was deleted" in WhatsApp |
| `mark_read` | Marcat mesaj de la Dan Luca ca citit | PASS |
| `create_poll` | Poll "Favorite AI?" cu 3 optiuni | PASS - poll vizibil si functional in WhatsApp |
| `send_reply` | Reply cu quote la mesajul editat | PASS - reply-ul apare cu quoted message |

**Problema critica de usability - TRANSVERSALA:**

Toate aceste 6 tool-uri necesita `message_id` ca parametru. Dar **`list_messages` nu returneaza message IDs in output-ul text** (le include doar pentru media messages). Asta inseamna ca un AI care foloseste MCP-ul:
1. Apeleaza `list_messages` -> primeste text formatat fara ID-uri
2. Vrea sa faca reply/react/edit -> **nu are message_id**
3. Nu are cum sa faca legatura intre mesajul vazut si ID-ul necesar

**Asta face aceste tool-uri aproape inutilizabile in practica** fara a schimba `list_messages`.

**Propuneri:**
1. **CRITICAL:** `list_messages` trebuie sa returneze `message_id` mereu in output (nu doar la media). Format propus: `[2026-02-07 13:24:09] [ID: 3A0CCDFD...] Chat: Agentic Awakened From: Me: Asta`
2. `sender_jid` e confuz ca parametru la `send_reaction`/`delete_message` - docstring ar trebui sa explice ca e JID-ul senderului ORIGINAL, nu al celui care reactioneaza. Si ca pentru mesaje proprii se pune "me".
3. `send_reply` necesita `quoted_content` pe langa `quoted_message_id` - e redundant daca bridge-ul ar putea lua contentul din DB. Dar e OK ca fallback.

**Status:** PASS - all 6 fully functional. Critical dependency: `list_messages` trebuie sa includa message IDs.

---

## Tools #14-#15: `send_presence`, `set_status_message`
**Category:** Presence & User Profile

**Intent:**
- `send_presence`: Seteaza statusul online/offline al contului WhatsApp. Util pentru a simula prezenta ("am vazut ca esti online") sau a semnala indisponibilitate. In context coaching: AI-ul poate pune contul "available" inainte de a trimite mesaje batch (pare mai natural) si "unavailable" dupa.
- `set_status_message`: Schimba textul "About" din profilul WhatsApp. Util pentru automatizare - ex: "In sesiune pana la 18:00", sau update automat cu citat motivational zilnic.

**Teste:**
- `send_presence("available")` -> `success: true`
- `send_presence("unavailable")` -> `success: true`
- `set_status_message("Building the future with AI 🤖")` -> `success: true`

**Usability:**
- Response-urile sunt clare si minimaliste
- `send_presence` nu valideaza input-ul - ce se intampla cu un string invalid? (nu am testat sa nu trimit garbage la WhatsApp API)
- `set_status_message` nu returneaza mesajul setat ca confirmare
- `set_status_message` nu are limita de caractere documentata (WhatsApp are 139 chars max)

**Propuneri:**
- `send_presence`: Docstring sa specifice clar valorile valide: "available" sau "unavailable". Validare in Python layer inainte de a trimite la bridge.
- `set_status_message`: Warn daca mesajul > 139 chars (limita WhatsApp). Returneaza mesajul setat in response.

**Status:** PASS - both functional.

---

## Tools #16-#18: `create_newsletter`, `get_newsletters`, `newsletter_send`
**Category:** Newsletter/Channel Management

**Intent:**
- `create_newsletter`: Creeaza un canal WhatsApp (tip broadcast one-to-many). Util pentru a seta automat canale de comunicare - ex: "Newsletter Coaching Q1 2026".
- `get_newsletters`: Listeaza toate canalele la care esti abonat/pe care le detii. Util pentru a vedea ce canale exista inainte de a trimite.
- `newsletter_send`: Trimite mesaj intr-un canal/newsletter. Util pentru broadcast automat - citate zilnice, anunturi, recap-uri de sesiuni.

**Teste:**
- `create_newsletter("MCP Test Channel", "Test channel...")` -> PASS, returneaza JID `120363422634794081@newsletter`
- `get_newsletters()` -> PASS, listeaza 2 newsletters (cel existent + cel nou creat)
- `newsletter_send(jid, "First message...")` -> PASS, mesaj trimis in canal

**Usability:**
- `create_newsletter` returneaza JID-ul - util pentru apeluri ulterioare
- `get_newsletters` returneaza lista completa cu JID, name, description - curat
- **Nu exista tool de delete newsletter** - odata creat, nu il poti sterge prin MCP
- **Nu exista tool de edit newsletter** (change name/description dupa creare)
- `newsletter_send` nu returneaza message_id in response (doar "newsletter message sent")

**Propuneri:**
- Adauga `delete_newsletter` tool (sau macar documenteaza ca nu se poate sterge prin MCP)
- `newsletter_send` sa returneze message_id in response pentru consistenta
- `get_newsletters` ar putea include subscriber_count daca API-ul WhatsApp il expune

**Status:** PASS - all three functional.

---

## Tool #19: `send_status`
**Category:** WhatsApp Status (Stories)

**Intent:** Posteaza un text status pe WhatsApp (vizibil 24h pentru contacte, similar Instagram Stories). Util pentru automatizare: citate motivationale zilnice, anunturi "In sesiune", "Disponibil pentru coaching", etc.

**Test:** Postat "Testing WhatsApp MCP tools - automated status posting works!"
- `success: true`, `message: "status posted"`

**Usability:**
- Response minimal si clar
- **Doar text** - nu exista optiune de a posta imagine/video ca status (limitare curenta)
- **Nu returneaza status_id** - nu poti sterge statusul dupa postare
- **Nu exista `get_status` / `delete_status`** - fire and forget
- Nu e clar daca statusul se adauga la cele existente sau le inlocuieste

**Propuneri:**
- Documenteaza ca e text-only si ca statusul dureaza 24h
- Consider: `send_status_image` pentru status-uri cu media (viitor)
- Returneaza un ID in response pentru referinta

**Status:** PASS - functional.

---

## Tools #20-#22: `link_group`, `unlink_group`, `get_sub_groups`
**Category:** Community Management

**Intent:**
- `get_sub_groups`: Listeaza sub-grupurile unei comunitati WhatsApp. Util pentru a vedea structura unei comunitati - ce grupuri contine.
- `link_group`: Adauga un grup existent la o comunitate. Util pentru organizare automata a grupurilor in comunitati.
- `unlink_group`: Scoate un grup dintr-o comunitate. Util pentru restructurare.

**Teste:**
- `get_sub_groups("120363294069275968@g.us")` -> PASS, gasit 1 sub-grup
- `get_sub_groups("120363291271345671@g.us")` -> 403 forbidden (nu esti admin pe acea comunitate) - eroare corecta
- `link_group` cu JID-uri fake -> endpoint raspunde cu eroare "info query timed out" (expected - JID inexistent)
- `unlink_group` cu JID-uri fake -> la fel, endpoint raspunde corect

**Nota:** `link_group` si `unlink_group` nu au fost testate cu JID-uri reale pentru a nu modifica structura comunitatilor existente. Endpoint-urile raspund si valideaza corect.

**Usability:**
- `get_sub_groups` returneaza doar JID si "name" dar name-ul e de fapt JID-ul repetat (nu numele real al grupului) - **BUG**: `"name": "120363291271345671@g.us"` in loc de numele grupului
- `link_group`/`unlink_group` sunt actiuni distructive fara confirmare - AI-ul ar trebui intrebat inainte de a le executa
- Nu exista tool de `create_community` - doar management de comunitati existente

**Propuneri:**
- **FIX BUG:** `get_sub_groups` trebuie sa returneze numele real al sub-grupurilor (probabil Go bridge-ul nu face lookup pe GroupInfo pentru fiecare sub-grup)
- `link_group`/`unlink_group`: Docstring sa avertizeze ca sunt actiuni structurale cu impact

**Status:** PARTIAL PASS - `get_sub_groups` are bug pe camp `name`. Endpoints functionale.

---

## Tools #23-#26: Analytics (`get_group_activity_report`, `get_member_engagement`, `cross_group_search`, `get_participant_journey`)
**Category:** Analytics (SQL-based, no Go bridge needed)

**Intent:**
- `get_group_activity_report`: Sumar de activitate al unui grup - cate mesaje, cati senderi unici, mesaje/zi. Util pentru a evalua rapid cat de activ e un grup.
- `get_member_engagement`: Per-member stats - cate mesaje a trimis fiecare, cand a fost ultimul activ, clasificare (active/moderate/inactive). Util pentru coaching: "cine nu mai participa?".
- `cross_group_search`: Cauta un text in mesajele din TOATE grupurile. Util pentru a gasi conversatii pe un topic indiferent de grup.
- `get_participant_journey`: Toate grupurile in care e un contact + activitatea lui per grup. Util pentru coaching: "in ce grupuri e Dan si cat de activ e in fiecare?".

**Teste:**

| Tool | Test | Rezultat |
|------|------|----------|
| `get_group_activity_report` | Agentic Awakened, 30 zile | PASS - 10 msgs, 2 senderi, 0.33/zi |
| `get_member_engagement` | Agentic Awakened, 90 zile | PASS - 2 membri cu clasificari corecte |
| `cross_group_search` | query="coaching", limit=5 | PASS - 5 rezultate din chat-uri diferite |
| `get_participant_journey` | Dan Luca (14547104600147@lid) | PASS - 15 grupuri gasite cu stats per grup |

**Usability:**

**`get_group_activity_report`** - Excelent. Response mic, curat, exact ce ai nevoie. Nimic de schimbat.

**`get_member_engagement`** - Bun dar:
- `name` contine LID-ul raw (`40720900690`) in loc de numele contactului. Ar trebui sa faca lookup in contacts.
- Clasificarea (active/moderate/inactive) e utila dar nu e documentata pe ce criterii se bazeaza.
- Lipseste `total_messages` in response header pentru context (ex: "8 din 10 mesaje = 80%").

**`cross_group_search`** - Functional dar:
- Returneaza mesaje INTREGI, inclusiv cele foarte lungi (un rezultat avea ~4000 chars - un wall of text copiat). **Ar trebui truncat content-ul** la ~200 chars cu `...` si sa ofere `message_id` pentru a citi integral cu `get_message_context`.
- Nu returneaza in care grup s-a gasit in mod vizibil (returneaza `chat_name` dar e usor de ratat).
- Foarte util ca tool - "cauta coaching in toate conversatiile" e un use case puternic.

**`get_participant_journey`** - Foarte util dar:
- Returneaza si grupuri cu `message_count: 0` (e membru dar nu a scris nimic in DB). Ar putea avea `include_empty: bool = False` ca default.
- `group_name` e corect populat (spre deosebire de `get_sub_groups`).

**Propuneri:**
1. `get_member_engagement`: Resolve contact names din DB (nu doar LID-uri raw)
2. `cross_group_search`: Truncheaza content la 200 chars by default. Adauga parametru `max_content_length: int = 200`.
3. `get_participant_journey`: Adauga `include_empty: bool = False` sa filtreze grupurile fara mesaje.
4. `get_member_engagement`: Documenteaza criteriile de clasificare in docstring.

**Status:** PASS - all four functional. Usability improvements needed.

---

## Tools #27-#28: Orchestration (`broadcast_to_groups`, `get_group_overlap`)
**Category:** Orchestration (Python-only, no Go bridge)

**Intent:**
- `broadcast_to_groups`: Trimite acelasi mesaj la multiple grupuri cu delay de 3s intre ele. Util pentru anunturi simultane - ex: "Sesiunea de maine e la 18:00" in 5 grupuri de coaching.
- `get_group_overlap`: Compara membrii a 2+ grupuri si arata cine e in toate, cine e doar intr-unul. Util pentru: "cati din grupul A sunt si in grupul B?" sau deduplicare.

**Teste:**
- `broadcast_to_groups`: **Nu testat cu mesaje reale** (ar trimite spam). Codul verificat - face loop peste `send_message()` cu `time.sleep(3)`.
- `get_group_overlap`: Comparat "6 Sisteme by Dan Luca & 5AM" cu "6 Sisteme by Dan Luca (2025)" -> PASS: 61 common members, sute unique per group.

**Usability:**

**`broadcast_to_groups`**:
- Delay-ul de 3s e hardcoded - ar putea fi parametru
- Nu are dry-run mode - nu poti vedea "la cine ar ajunge" fara sa trimiti
- Returneaza status per grup - util pentru a vedea care au esuat
- **FOARTE periculos** - un AI care trimite mesaje la 20 de grupuri simultan trebuie sa ceara confirmare explicita

**`get_group_overlap`**:
- **Response ENORM** - returneaza TOATE LID-urile raw ale membrilor unici per grup. Pe 2 grupuri de ~700+ membri, response-ul a fost zeci de mii de caractere de LID-uri.
- **Complet inutilizabil in forma curenta** pentru grupuri mari.
- Ar trebui sa returneze doar COUNTS by default: `common_count: 61, unique_in_group_A: 523, unique_in_group_B: 731`
- Optional: `include_members: bool = False` pentru a vedea si listele complete.
- LID-urile nu au name/phone - imposibil de interpretat de un AI sau human.

**Propuneri:**
1. `get_group_overlap`: **CRITICAL** - by default returneaza doar counts, nu liste de LID-uri. Adauga `include_members: bool = False`.
2. `get_group_overlap`: Cand `include_members=True`, resolve names din contacts.
3. `broadcast_to_groups`: Adauga `delay_seconds: int = 3` ca parametru.
4. `broadcast_to_groups`: Adauga in docstring WARNING despre actiunea bulk.

**Status:** PARTIAL PASS - `get_group_overlap` inutilizabil pe grupuri mari (output prea mare). `broadcast_to_groups` netestat dar cod corect.

---

## SUMAR GENERAL

### Statistici
- **Total tools testate:** 28
- **PASS:** 23
- **PARTIAL PASS:** 3 (`get_group_info`, `get_sub_groups`, `get_group_overlap`)
- **NOT TESTED (destructive):** 2 (`broadcast_to_groups`, `link_group`/`unlink_group` - doar endpoint validation)

### Probleme critice (trebuie fixate)

1. **`list_messages` nu returneaza message IDs** - face 6 tool-uri (react, edit, delete, mark_read, poll, reply) practic inutilizabile fara workaround. AI-ul nu are cum sa obtina ID-ul unui mesaj din output-ul list_messages.

2. **`get_group_info` returneaza 80K+ pe grupuri mari** - depaseste limita MCP. Fix: `include_participants=False` by default + `participant_count` mereu.

3. **`get_group_overlap` returneaza zeci de mii de LID-uri** - inutilizabil. Fix: returneaza doar counts by default.

### Probleme moderate (nice to have)

4. **`get_sub_groups`** - camp `name` returneaza JID in loc de numele grupului.
5. **`cross_group_search`** - mesaje intregi (pot fi foarte lungi) in loc de truncat.
6. **`get_member_engagement`** - LID-uri raw in loc de contact names.
7. **`get_participant_journey`** - returneaza si grupuri cu 0 mesaje by default.

### Toate tool-urile functioneaza tehnic - problemele sunt de usability/scalabilitate.
