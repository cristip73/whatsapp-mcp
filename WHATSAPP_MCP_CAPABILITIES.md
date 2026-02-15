# WhatsApp MCP - Lista Completă de Funcționalități

Acest document prezintă toate capacitățile expuse de WhatsApp MCP Server, împreună cu exemple practice de utilizare.

---

## 📇 Gestionare Contacte

### 1. `search_contacts`
**Descriere:** Caută contacte WhatsApp după nume sau număr de telefon.

**Use case:** *Vrei să trimiți un mesaj lui Ion Popescu dar nu-i știi numărul exact. Cauți "Ion" și primești lista tuturor contactelor care conțin acest nume, cu JID-ul lor pentru a putea trimite mesaje.*

---

## 💬 Operațiuni cu Mesaje

### 2. `list_messages`
**Descriere:** Obține mesaje WhatsApp bazat pe criterii multiple: interval de timp, expeditor, chat, sau căutare text. Suportă paginare și context în jurul rezultatelor.

**Use case:** *Ai nevoie să găsești toate mesajele din ultima săptămână care menționează "factură" pentru a verifica ce facturi ai de plătit. Cauți cu `query="factură"` și `after="2025-01-16"` pentru a le lista.*

---

### 3. `get_message_context`
**Descriere:** Obține mesajele din jurul unui mesaj specific (înainte și după).

**Use case:** *Ai găsit un mesaj important dar vrei să înțelegi contextul conversației. Folosești această funcție cu ID-ul mesajului pentru a vedea cele 5 mesaje înainte și după.*

---

## 📱 Gestionare Chat-uri

### 4. `list_chats`
**Descriere:** Listează toate chat-urile WhatsApp, cu opțiuni de filtrare, sortare și paginare.

**Use case:** *Vrei să vezi care sunt cele mai recente 10 conversații active pentru a le răspunde. Sortezi după `last_active` și limitezi la 10.*

---

### 5. `get_chat`
**Descriere:** Obține metadatele unui chat specific după JID.

**Use case:** *Vrei să verifici numele grupului "Familie" și ultimul mesaj trimis acolo pentru a vedea dacă ai ratat ceva important.*

---

### 6. `get_direct_chat_by_contact`
**Descriere:** Găsește chat-ul direct cu o persoană folosind numărul de telefon.

**Use case:** *Ai numărul +40721234567 și vrei să accesezi conversația directă cu acea persoană fără să cauți manual prin toate chat-urile.*

---

### 7. `get_contact_chats`
**Descriere:** Obține toate chat-urile în care apare un contact (inclusiv grupuri comune).

**Use case:** *Vrei să vezi în ce grupuri ești împreună cu colegul Andrei pentru a-i trimite un mesaj în grupul potrivit.*

---

### 8. `get_last_interaction`
**Descriere:** Găsește cel mai recent mesaj cu un contact specific.

**Use case:** *Ți-ai amintit că trebuia să răspunzi cuiva și vrei să vezi când a fost ultima dată când ai vorbit cu Maria pentru a relua conversația.*

---

## ✉️ Trimitere Mesaje

### 9. `send_message`
**Descriere:** Trimite un mesaj text către o persoană sau grup.

**Use case:** *Vrei să trimiți automat un mesaj de "Bună dimineața!" grupului de familie în fiecare zi, sau să confirmi o programare unui client.*

---

### 10. `send_file`
**Descriere:** Trimite fișiere (imagini, video, documente) prin WhatsApp.

**Use case:** *Trebuie să trimiți contractul PDF unui client sau să partajezi pozele de la petrecere în grupul de prieteni.*

---

### 11. `send_audio_message`
**Descriere:** Trimite un fișier audio ca mesaj vocal WhatsApp (convertește automat în format Opus).

**Use case:** *Ai înregistrat un memo vocal și vrei să-l trimiți ca mesaj vocal (nu ca fișier atașat) pentru ca destinatarul să-l poată asculta direct în chat.*

---

## 📥 Media

### 12. `download_media`
**Descriere:** Descarcă media dintr-un mesaj WhatsApp (poze, video, documente) pe disc local.

**Use case:** *Cineva ți-a trimis poze importante de la eveniment și vrei să le salvezi local pentru backup sau procesare ulterioară.*

---

## 👥 Gestionare Grupuri

### 13. `create_group`
**Descriere:** Creează un grup WhatsApp nou cu participanții specificați.

**Use case:** *Organizezi o excursie și vrei să creezi rapid grupul "Excursie Munte 2025" cu cei 15 participanți, fără să-i adaugi manual unul câte unul.*

---

### 14. `join_group_with_link`
**Descriere:** Te alătură unui grup folosind un link de invitație.

**Use case:** *Ai primit un link de invitație pentru grupul comunității locale și vrei să te înscrii automat.*

---

### 15. `leave_group`
**Descriere:** Părăsești un grup WhatsApp.

**Use case:** *Ai terminat proiectul și vrei să părăsești grupul de lucru care nu mai este relevant.*

---

### 16. `update_group_participants`
**Descriere:** Adaugă, elimină, promovează sau retrogradează participanți într-un grup.

**Acțiuni disponibile:**
- `add` - adaugă membri
- `remove` - elimină membri
- `promote` - promovează la admin
- `demote` - retrogradează din admin

**Use case:** *Ești admin al grupului de clasă și trebuie să adaugi 3 colegi noi, să elimini pe cineva care a plecat, și să promovezi încă un admin care să te ajute să moderezi discuțiile.*

---

### 17. `set_group_name`
**Descriere:** Schimbă numele unui grup WhatsApp.

**Use case:** *Grupul "Proiect Alpha" s-a terminat și vrei să-l redenumești în "Proiect Beta" pentru noul proiect cu aceeași echipă.*

---

### 18. `set_group_photo`
**Descriere:** Schimbă poza de profil a unui grup.

**Use case:** *Ai creat un logo nou pentru echipa de fotbal și vrei să-l setezi ca imagine a grupului.*

---

## 📊 Sumar Funcționalități

| Categorie | Funcții | Total |
|-----------|---------|-------|
| Contacte | `search_contacts` | 1 |
| Mesaje | `list_messages`, `get_message_context` | 2 |
| Chat-uri | `list_chats`, `get_chat`, `get_direct_chat_by_contact`, `get_contact_chats`, `get_last_interaction` | 5 |
| Trimitere | `send_message`, `send_file`, `send_audio_message` | 3 |
| Media | `download_media` | 1 |
| Grupuri | `create_group`, `join_group_with_link`, `leave_group`, `update_group_participants`, `set_group_name`, `set_group_photo` | 6 |
| **TOTAL** | | **18** |

---

## 🔧 Cerințe Tehnice

- **Go WhatsApp Bridge** trebuie să ruleze înainte de serverul MCP
- Prima rulare necesită autentificare prin scanarea codului QR
- Re-autentificare necesară aproximativ la 20 de zile
- FFmpeg necesar pentru conversia audio la mesaje vocale
- Fișierele media sunt stocate local după descărcare

---

*Generat automat - Ianuarie 2025*
