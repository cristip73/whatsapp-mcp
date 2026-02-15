# WhatsApp MCP Server - Roadmap & Feature Analysis

> Report generat pe 15 Februarie 2026
> Focalizat pe use-case: **Firma de coaching cu grupuri multiple pe cohorte**

---

## Starea Actuala: 20 MCP Tools Implementate

| # | Tool | Ce face | Backend | Status |
|---|------|---------|---------|--------|
| 1 | `search_contacts` | Cauta contacte dupa nume/telefon | SQLite | OK |
| 2 | `list_messages` | Mesaje cu filtre (data, sender, chat, query) | SQLite | OK |
| 3 | `list_chats` | Lista chat-uri cu paginare si sortare | SQLite | OK |
| 4 | `get_chat` | Metadata chat dupa JID | SQLite | OK |
| 5 | `get_direct_chat_by_contact` | Chat direct dupa telefon | SQLite | OK |
| 6 | `get_contact_chats` | Toate chat-urile cu un contact | SQLite | OK |
| 7 | `get_contact_groups` | **Grupuri comune cu un contact (LIVE)** | HTTP API | **NOU** |
| 8 | `get_last_interaction` | Ultimul mesaj cu un contact | SQLite | OK |
| 9 | `get_message_context` | Mesaje din jurul unui mesaj specific | SQLite | OK |
| 10 | `send_message` | Trimite mesaj text | HTTP API | OK |
| 11 | `send_file` | Trimite imagine/video/document | HTTP API | OK |
| 12 | `send_audio_message` | Trimite mesaj audio (Opus .ogg) | HTTP API | OK |
| 13 | `download_media` | Descarca media dintr-un mesaj | HTTP API | OK |
| 14 | `create_group` | Creeaza grup nou | HTTP API | OK |
| 15 | `join_group_with_link` | Intra in grup cu link | HTTP API | OK |
| 16 | `leave_group` | Paraseste grup | HTTP API | OK |
| 17 | `update_group_participants` | Add/remove/promote/demote participanti | HTTP API | OK |
| 18 | `set_group_name` | Schimba numele grupului | HTTP API | OK |
| 19 | `set_group_photo` | Schimba poza grupului | HTTP API | OK |

---

## Buguri Cunoscute de Rezolvat

| # | Bug | Severitate | Detalii |
|---|-----|-----------|---------|
| B1 | **Dublu `file://` in `download_media`** | HIGH | `whatsapp.py` adauga `file://`, apoi `main.py` adauga iar. Rezultat: `file://file:///path` |
| B2 | **`list_messages` returneaza string, nu List[Dict]** | MEDIUM | Semnatura zice `List[Message]` dar `format_messages_list()` returneaza string |
| B3 | **N+1 query in `get_message_context`** | MEDIUM | 20 mesaje cu context = 60 query-uri separate |
| B4 | **Lipsesc indexuri in DB** | MEDIUM | Doar PRIMARY KEY, fara indexuri pe `chat_jid + timestamp` sau `sender` |

---

## Propuneri Noi - Organizate pe Prioritate si Utilitate

### TIER 1 - Impact Maxim pentru Coaching (Implementeaza Prima)

#### 1. `get_group_info` / `get_group_participants` - Lista participanti grup
| | |
|---|---|
| **Ce face** | Returneaza toti membrii unui grup cu rol (admin/membru), telefon, nume |
| **Utilitate coaching** | Fundament pentru ORICE analytics de grup. Stii exact cine e in fiecare cohorta |
| **Efort** | Mic - whatsmeow `GetGroupInfo()` returneaza deja `Participants []GroupParticipant` |
| **Prioritate** | **CRITICA** - toate celelalte features depind de asta |

#### 2. `create_poll` - Creeaza poll nativ WhatsApp
| | |
|---|---|
| **Ce face** | Trimite poll cu intrebare + optiuni in orice grup |
| **Utilitate coaching** | Check-in-uri zilnice ("La cat te-ai trezit?"), feedback sesiuni, voting teme. Poll-urile native WhatsApp au 80%+ rata de raspuns |
| **Efort** | Mediu - whatsmeow suporta `BuildPollCreation()` cu optiuni, quiz mode, expiration |
| **Proto** | `PollCreationMessage { name, options[], selectableOptionsCount, endTime, correctAnswer }` |
| **Prioritate** | **FOARTE MARE** - cel mai puternic tool de engagement |

#### 3. `send_reaction` - Reactioneaza la mesaje
| | |
|---|---|
| **Ce face** | Trimite emoji reactie la un mesaj specific |
| **Utilitate coaching** | Acknowledging check-in-uri - un emoji pe selfie-ul de 5AM e mic dar are impact urias pe engagement |
| **Efort** | Mic - whatsmeow `BuildReaction(chat, sender, id, emoji)` |
| **Prioritate** | **MARE** - effort mic, impact mare |

#### 4. `broadcast_to_groups` - Trimite mesaj la multiple grupuri
| | |
|---|---|
| **Ce face** | Trimite acelasi mesaj la N grupuri cu rate limiting (2-5s intre mesaje) |
| **Utilitate coaching** | "Trimite programul saptamanii la toate grupurile 5AM" - transforma 30 min munca manuala in 10 secunde |
| **Efort** | Mic - orchestrare Python peste `send_message` existent |
| **Prioritate** | **MARE** - salvare timp imediata |

#### 5. `get_group_activity_report` - Raport activitate grup
| | |
|---|---|
| **Ce face** | Nr mesaje, senderi unici, mesaje/zi, membri activi vs silentiosi - per grup, pe o perioada |
| **Utilitate coaching** | "Care cohorte sunt active si care mor?" - identifica interventia necesara |
| **Efort** | Mic - SQL queries pe DB-ul existent, fara Go bridge |
| **Prioritate** | **MARE** - actionable insights imediate |

---

### TIER 2 - Valoare Mare, Efort Moderat

#### 6. `edit_message` - Editeaza mesaje trimise
| | |
|---|---|
| **Ce face** | Modifica un mesaj deja trimis |
| **API** | `Client.BuildEdit(chat, id, newContent)` |
| **Utilitate** | Fix typos in anunturi de grup fara "corectie: ..." |

#### 7. `delete_message` - Sterge mesaje
| | |
|---|---|
| **Ce face** | Revoca un mesaj (delete for everyone) |
| **API** | `Client.BuildRevoke(chat, sender, id)` |
| **Utilitate** | Curatenie in grupuri, sterge mesaje trimise gresit |

#### 8. `reply_to_message` - Raspunde la un mesaj specific
| | |
|---|---|
| **Ce face** | Trimite mesaj cu quote/reply la un mesaj anterior |
| **API** | Set `ContextInfo.QuotedMessage` + `StanzaID` |
| **Utilitate** | Raspunsuri contextuale in conversatii de grup active |

#### 9. `get_group_invite_link` - Genereaza link invitare
| | |
|---|---|
| **Ce face** | Obtine/regenereaza link-ul de invitare al unui grup |
| **API** | `Client.GetGroupInviteLink(ctx, jid, reset)` |
| **Utilitate** | Genereaza link-uri fresh pentru pagini de enrollment cohorte noi |

#### 10. `set_group_description` - Seteaza descrierea grupului
| | |
|---|---|
| **Ce face** | Actualizeaza topic/descrierea unui grup |
| **API** | `Client.SetGroupTopic()` / `Client.SetGroupDescription()` |
| **Utilitate** | Update dinamic al regulilor/info-ului cohortei |

#### 11. `set_group_announce` - Mod "doar adminii posteaza"
| | |
|---|---|
| **Ce face** | Toggle intre "toti pot posta" si "doar adminii" |
| **API** | `Client.SetGroupAnnounce(ctx, jid, announce)` |
| **Utilitate** | Sesiuni structurate: blocheaza chat-ul, prezinta, deblocheaza pentru Q&A |

#### 12. `check_phone_on_whatsapp` - Verifica daca numarul e pe WhatsApp
| | |
|---|---|
| **Ce face** | Valideaza numere de telefon inainte de a le adauga in grupuri |
| **API** | `Client.IsOnWhatsApp(phones)` |
| **Utilitate** | Evita erori la onboarding - verifica inainte de add |

---

### TIER 3 - Analytics si Monitorizare Avansata

#### 13. `get_member_engagement` - Scor engagement per membru
| | |
|---|---|
| **Ce face** | Pentru un grup: lista toti participantii cu nr mesaje, ultima activitate, clasificare (activ/low/silent) |
| **Utilitate** | Identifica membrii la risc de churn. Fiecare membru retinut = venit recurent |
| **Implementare** | Combina `get_group_participants` cu SQL pe messages table |

#### 14. `cross_group_search` - Cauta mesaje in toate grupurile
| | |
|---|---|
| **Ce face** | Cauta un keyword in toate grupurile (sau grupuri dupa pattern) simultan |
| **Utilitate** | "Unde s-a discutat despre retreat?" - gaseste instant fara sa cauti grup cu grup |
| **Implementare** | Enhance `list_messages` sa accepte `chat_jid_pattern` cu LIKE |

#### 15. `get_participant_journey` - Istoricul unui participant
| | |
|---|---|
| **Ce face** | Toate grupurile unui contact + activitatea in fiecare + timeline |
| **Utilitate** | Vede progresul: HERO#15 -> INVINCIBLE 2023 -> Retreat 2025. Upsell opportunities |

#### 16. `get_group_overlap` - Membri comuni intre grupuri
| | |
|---|---|
| **Ce face** | Compara 2+ grupuri si arata cine e in ambele/unic |
| **Utilitate** | "Cine din HERO#18 nu a intrat inca in INVINCIBLE 2024?" |

#### 17. `mark_as_read` - Marcheaza mesaje ca citite
| | |
|---|---|
| **Ce face** | Blue ticks pe mesaje/chat-uri |
| **API** | `Client.MarkRead(ids, timestamp, chat, sender)` |
| **Utilitate** | Igiena inbox - marcheaza automat chat-urile procesate |

---

### TIER 4 - Features Strategice pe Termen Lung

#### 18. Newsletter / Channel Management
| | |
|---|---|
| **Ce face** | Creeaza si administreaza WhatsApp Channels (broadcast unidirectional) |
| **API** | `CreateNewsletter`, `GetSubscribedNewsletters`, `GetNewsletterMessages`, etc. |
| **Utilitate** | "5AM Club Official" channel - anunturi care ajung la toti fara reply clutter. Suporta pana la 5000 followeri |

#### 19. Community Management
| | |
|---|---|
| **Ce face** | Creeaza Communities care grupeaza multiple grupuri sub o umbrela |
| **API** | `CreateGroup(IsParent: true)`, `LinkGroup()`, `GetSubGroups()`, `GetLinkedGroupsParticipants()` |
| **Utilitate** | O singura "5AM Club" Community cu sub-grupuri per cohorta. Announcement group ajunge la toti |

#### 20. Label Management (CRM-like)
| | |
|---|---|
| **Ce face** | Taguri pe chat-uri si mesaje (ca in WhatsApp Business) |
| **API** | `appstate.BuildLabelEdit/BuildLabelChat/BuildLabelMessage` |
| **Utilitate** | Categorizeaza participanti: "VIP", "Risc churn", "Upsell candidate" |

#### 21. Event-Driven Automation
| | |
|---|---|
| **Ce face** | Detecteaza evenimente (membru nou in grup, mesaj primit) si reactioneaza automat |
| **API** | Event handlers: `events.GroupInfo`, `events.JoinedGroup`, `events.Receipt` |
| **Utilitate** | Welcome messages automate, nudge-uri la inactivitate, tracking read receipts |

#### 22. Status/Story Posting
| | |
|---|---|
| **Ce face** | Posteaza pe WhatsApp Status (vizibil 24h tuturor contactelor) |
| **API** | `SendMessage` to `types.StatusBroadcastJID` |
| **Utilitate** | Citate motivationale zilnice, "challenge of the day" |

---

## Comparatie cu Competitia

| Feature | **Noi (20 tools)** | Extended MCP (41 tools) | WAHA MCP (63 tools) | Periskope ($49-199/mo) |
|---|:---:|:---:|:---:|:---:|
| Mesagerie de baza | YES | YES | YES | YES |
| Grup management | YES | YES | YES | YES |
| **Contact groups (LIVE)** | **YES** | NO | NO | NO |
| Send reaction | NO | YES | YES | YES |
| Edit/delete mesaje | NO | YES | YES | NO |
| Create poll | NO | YES | YES | NO |
| Get group participants | NO | YES | YES | YES |
| Group invite links | NO | NO | YES | NO |
| Newsletters/Channels | NO | YES | NO | NO |
| Labels/CRM | NO | NO | YES | YES |
| Group analytics | NO | NO | NO | YES |
| Multi-group broadcast | NO | NO | NO | YES |
| AI-native reasoning | **YES** | NO | NO | NO |

**Avantajul nostru unic**: AI-native. Claude poate rationa despre date, compune mesaje personalizate, si lua decizii ("acest membru pare dezangajat bazat pe frecventa in scadere - sa ii trimit un check-in?"). Niciun dashboard tool nu poate face asta.

---

## Capabilitati whatsmeow Disponibile dar Neimplementate

### Mesagerie Avansata
- `BuildEdit()` - editare mesaje
- `BuildRevoke()` - stergere mesaje
- `BuildReaction()` - reactii emoji
- `PollCreationMessage` - poll-uri cu quiz mode, expiration, hide names
- `ListMessage` / `ButtonsMessage` - mesaje interactive cu butoane
- `LocationMessage` / `LiveLocationMessage` - share locatie
- `ContactMessage` - share contact
- `StickerMessage` - stickere
- `ViewOnceMessage` - mesaje view-once

### Grup & Community
- `GetGroupInfo()` - info + lista participanti
- `GetGroupInviteLink()` / `RevokeGroupInviteLink()`
- `SetGroupTopic()` / `SetGroupDescription()`
- `SetGroupAnnounce()` - mod admin-only
- `SetGroupLocked()` - doar adminii editeaza info
- `SetGroupJoinApprovalMode()` - aprobare join
- `GetGroupRequestParticipants()` / `UpdateGroupRequestParticipants()`
- `LinkGroup()` / `UnlinkGroup()` - community management
- `GetSubGroups()` / `GetLinkedGroupsParticipants()`

### Newsletter / Channel
- `CreateNewsletter()`, `FollowNewsletter()`, `UnfollowNewsletter()`
- `GetNewsletterInfo()`, `GetSubscribedNewsletters()`
- `GetNewsletterMessages()`, `GetNewsletterMessageUpdates()`

### Presence & Receipts
- `SendPresence()` - online/offline
- `SubscribePresence()` - tracking
- `SendChatPresence()` - typing indicator
- `MarkRead()` - blue ticks
- `SetForceActiveDeliveryReceipts()`

### User Management
- `IsOnWhatsApp()` - verificare numar
- `GetUserInfo()` - avatar, status, devices
- `GetProfilePictureInfo()` - poza profil
- `SetStatusMessage()` - schimba "About"
- `GetBlocklist()` / `UpdateBlocklist()`
- `GetPrivacySettings()` / `SetPrivacySetting()`

### App State (Sync)
- Labels: `BuildLabelEdit`, `BuildLabelChat`, `BuildLabelMessage`
- Chat ops: `BuildMute`, `BuildPin`, `BuildArchive`, `BuildMarkChatAsRead`
- `BuildStar` - star/unstar mesaje
- `BuildDeleteChat`

### Events Disponibile dar Nehandled
- `events.Receipt` - read/delivery receipts
- `events.ChatPresence` - typing indicators
- `events.Presence` - user online/offline
- `events.GroupInfo` - modificari metadata grup
- `events.JoinedGroup` - intrat/adaugat in grup
- `events.LabelEdit` / `events.LabelAssociationChat`
- `events.CallOffer` - apeluri primite

---

## Recomandare de Implementare

**Primele 5 features de implementat** (in ordine):

1. **`get_group_info`** - fundament, efort mic, depinde totul de asta
2. **`create_poll`** - engagement maxim, diferentiator major
3. **`send_reaction`** - efort minim, valoare disproportionata
4. **`broadcast_to_groups`** - time-saver imediat, doar Python
5. **`get_group_activity_report`** - analytics fara Go changes, doar SQL

Acestea 5 ar transforma MCP-ul dintr-un tool de mesagerie intr-o **platforma de management coaching**.
