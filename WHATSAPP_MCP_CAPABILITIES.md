# WhatsApp MCP - Complete Capabilities Report

> **Your AI assistant, fully connected to WhatsApp.**
> 40 tools. Messaging, groups, analytics, automation -- all through natural conversation.

---

## PART 1: Tool Catalog

Every tool your AI assistant can use, explained in plain language.

---

### Messages & Conversations (11 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 1 | **search_contacts** | Finds WhatsApp contacts by name or phone number. | "Find everyone named Maria in my contacts." |
| 2 | **list_messages** | Retrieves messages with filters (date range, sender, keyword, chat). Shows message IDs for follow-up actions. | "Show me the last 20 messages in the coaching group." |
| 3 | **list_chats** | Lists all your WhatsApp conversations, sorted by recent activity or name. | "Which chats have been most active this week?" |
| 4 | **get_chat** | Gets details about a specific conversation (name, last message, timestamps). | "Pull up info on the 6 Sisteme group." |
| 5 | **get_direct_chat_by_contact** | Finds a 1-on-1 conversation using just a phone number. | "Find my DM history with +40730883388." |
| 6 | **get_message_context** | Shows messages before and after a specific message -- like viewing the full conversation around one reply. | "Show me 10 messages around that question Dan asked." |
| 7 | **send_message** | Sends a text message to any person or group. | "Send 'Session starts at 6 PM' to the coaching group." |
| 8 | **send_file** | Sends a photo, video, document, or any file via WhatsApp. | "Send this PDF workbook to the new member." |
| 9 | **send_audio_message** | Sends an audio file as a WhatsApp voice message (auto-converts format). | "Send this voice note recording to the group." |
| 10 | **download_media** | Downloads a photo, video, or file from a WhatsApp message to your computer. | "Download the image that Maria shared yesterday." |
| 11 | **get_last_interaction** | Finds the most recent message involving a specific contact. | "When was the last time I heard from Ion?" |

---

### Contacts & Search (5 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 12 | **get_contact_chats** | Shows every conversation a contact appears in (groups and DMs). | "What groups is Dan part of?" |
| 13 | **get_contact_groups** | Lists all WhatsApp groups where both you and a contact are members (live data, not just message history). | "Show me all groups I share with Maria." |
| 14 | **is_on_whatsapp** | Checks if one or more phone numbers are actually registered on WhatsApp. Works in batches. | "From this list of 50 new clients, how many have WhatsApp?" |
| 15 | **get_direct_chat_by_contact** | Looks up a private conversation using a phone number. | "Find my DM chat with this number: 40720900690." |
| 16 | **cross_group_search** | Searches for a word or phrase across ALL your groups at once. Like a global search engine for your WhatsApp. | "Find every message mentioning 'mindset' across all groups." |

---

### Groups & Communities (14 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 17 | **create_group** | Creates a brand new WhatsApp group with specified members. | "Create a group called 'VIP Coaching Q2' with these 5 people." |
| 18 | **get_group_info** | Gets a group's name, description, settings, and member count. Can optionally list members with pagination. | "How many people are in the 6 Sisteme 2025 group?" |
| 19 | **get_group_invite_link** | Gets the shareable invite link for a group. Can reset it if the old link was compromised. | "Get me the invite link for the coaching group so I can share it." |
| 20 | **set_group_name** | Renames a WhatsApp group. | "Rename the group to '6 Sisteme - Spring 2026'." |
| 21 | **set_group_photo** | Updates the group's profile picture. | "Set this logo as the group photo." |
| 22 | **set_group_topic** | Sets or updates the group description (the text visible under the group name). | "Update the group description with this week's schedule." |
| 23 | **set_group_announce** | Turns "admin-only messaging" on or off. When on, only admins can send messages. | "Put the group in announcement mode for the live session." |
| 24 | **set_group_locked** | Controls whether only admins can edit group info (name, photo, description). | "Lock the group info so members can't change the name." |
| 25 | **set_group_join_approval** | Turns on/off admin approval for new members joining via invite link. | "Enable join approval -- I want to vet new members before they enter." |
| 26 | **join_group_with_link** | Joins a group using an invite link. | "Join this group: https://chat.whatsapp.com/AbCdEf." |
| 27 | **leave_group** | Leaves a WhatsApp group. | "Leave the test group, I no longer need to be there." |
| 28 | **update_group_participants** | Adds, removes, promotes, or demotes members in a group. | "Promote Maria to admin in the coaching group." |
| 29 | **link_group** | Connects a group to a WhatsApp Community (the umbrella structure). | "Add the Q2 coaching group under the main community." |
| 30 | **unlink_group** | Removes a group from a WhatsApp Community. | "Detach the archived group from the community." |

---

### Reactions, Replies & Engagement (5 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 31 | **send_reaction** | Reacts to any message with an emoji. Can also remove a reaction. | "React with a fire emoji to Dan's motivational post." |
| 32 | **send_reply** | Replies to a specific message with a quoted reference (so everyone sees what you're responding to). | "Reply to Maria's question with this answer, quoting her original message." |
| 33 | **edit_message** | Edits a message you previously sent (the corrected version replaces the original). | "Fix the typo in my last message -- change 6PM to 7PM." |
| 34 | **delete_message** | Deletes/revokes a message so it disappears for everyone. | "Delete that accidental message I just sent." |
| 35 | **mark_read** | Marks messages as read (the blue checkmarks). | "Mark all unread messages in the coaching group as read." |

---

### Polls & Surveys (1 tool)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 36 | **create_poll** | Creates a WhatsApp poll with a question and multiple-choice options. Supports single or multiple selections. | "Create a poll: 'Best time for next session?' with options Morning, Afternoon, Evening." |

---

### Newsletters & Channels (3 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 37 | **create_newsletter** | Creates a new WhatsApp Channel (one-way broadcast channel, similar to a Telegram channel). | "Create a channel called 'Coaching Daily Insights'." |
| 38 | **get_newsletters** | Lists all the WhatsApp Channels you own or subscribe to. | "What channels do I have?" |
| 39 | **newsletter_send** | Publishes a message to a WhatsApp Channel. | "Send today's motivational quote to the Daily Insights channel." |

---

### Analytics & Insights (4 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 40 | **get_group_activity_report** | Shows a summary of group activity over a time period: total messages, unique participants, messages per day. | "How active was the coaching group in the last 30 days?" |
| 41 | **get_member_engagement** | Breaks down activity per member: who's active, who's quiet, who stopped participating. Classifies each member as very active, active, moderate, or inactive. | "Who are the top contributors in my coaching group? Who hasn't posted in a month?" |
| 42 | **get_participant_journey** | Shows everything about one person across ALL your groups: which groups they're in, how active they are in each, when they last participated. | "Give me a 360-degree view of Dan's participation across all groups." |
| 43 | **get_group_overlap** | Compares 2 or more groups and shows how many members they share. Helps find duplicates or understand audience overlap. | "How many people from the 2024 cohort are also in the 2025 cohort?" |

---

### Presence & Profile (2 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 44 | **send_presence** | Sets your WhatsApp status to "online" or "offline." | "Go online before sending the broadcast, then go offline after." |
| 45 | **set_status_message** | Changes the "About" text in your WhatsApp profile (the line under your name). Max 139 characters. | "Update my status to 'In coaching session until 18:00'." |

---

### WhatsApp Status / Stories (1 tool)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 46 | **send_status** | Posts a text message to your WhatsApp Status (like Instagram Stories -- visible for 24 hours to all your contacts). | "Post a motivational quote to my Status." |

---

### Bulk Operations (1 tool)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 47 | **broadcast_to_groups** | Sends the same message to multiple groups at once, with a built-in delay between sends to avoid rate limits. | "Announce the schedule change to all 5 coaching groups." |

---

### Community Management (2 tools)

| # | Tool | What it does | When you'd use it |
|---|------|-------------|-------------------|
| 48 | **get_sub_groups** | Lists all the groups that belong to a WhatsApp Community. | "What groups are under the '6 Sisteme' community umbrella?" |
| *(link_group / unlink_group are listed under Groups above)* | | |

---

> **Total: 48 tool entries** (some tools appear in multiple categories because they serve dual purposes).
> **Unique tools: 40** defined in the MCP server.

---

## PART 2: User Stories & Use Cases

Real scenarios for a coaching business running multiple WhatsApp groups with 500-800+ members each.

---

### Story 1: Morning Coaching Broadcast

**The Scenario:** Every Monday morning, the coach wants to send a motivational message plus a poll to 5 coaching cohort groups simultaneously, then post the same message to their WhatsApp Status and newsletter channel.

**Step-by-step flow:**

```
Step 1  list_chats (query="6 Sisteme")
        --> Finds all 5 coaching groups by name

Step 2  broadcast_to_groups (group_jids=[...5 groups], message="Good morning!
        This week's focus: consistency over perfection...")
        --> Sends the motivational message to all 5 groups, 3 seconds apart

Step 3  For each group:
        create_poll (question="What's YOUR #1 goal this week?",
                     options=["Health", "Business", "Relationships", "Mindset"])
        --> Creates an engagement poll in each group

Step 4  send_status ("This week's coaching theme: Consistency over Perfection")
        --> Posts to WhatsApp Status (visible 24h to all contacts)

Step 5  get_newsletters() --> find the coaching channel
        newsletter_send (message="Weekly Theme: Consistency over Perfection...")
        --> Publishes to the broadcast channel for subscribers

Step 6  send_presence ("unavailable")
        --> Goes offline after the batch sends are done
```

**Business value:** What used to take 30 minutes of manual copy-paste across 5 groups, a Status post, and a newsletter message now happens in one AI conversation. The coach just says "do the Monday morning broadcast" and the AI handles all of it.

---

### Story 2: New Member Onboarding

**The Scenario:** A new coaching client just signed up. The coach gives the AI their phone number and says "onboard them."

**Step-by-step flow:**

```
Step 1  is_on_whatsapp (phones=["+40720555123"])
        --> Checks if they have WhatsApp. Returns: yes, registered.

Step 2  search_contacts ("40720555123")
        --> Finds the contact, gets their name: "Elena Popescu"

Step 3  send_message (recipient="40720555123",
                      message="Welcome to the coaching program, Elena!")
        --> Personal welcome DM

Step 4  get_group_invite_link (jid="coaching_group_2026@g.us")
        --> Gets the current invite link

Step 5  send_message (recipient="40720555123",
                      message="Here's your group link: https://chat.whatsapp.com/...")
        --> Sends the group invite privately

Step 6  set_group_join_approval (jid="...", mode=true)
        --> Makes sure admin approval is on (if not already)

Step 7  send_file (recipient="40720555123",
                   media_path="/path/to/welcome_guide.pdf")
        --> Sends the onboarding PDF workbook
```

**Business value:** Zero-touch onboarding. The coach types "add Elena, +40720555123, to the 2026 cohort" and the AI handles verification, welcome message, group invite, and materials delivery. No manual steps, no forgotten PDFs.

---

### Story 3: Weekly Engagement Health Check

**The Scenario:** Every Friday, the coach wants a quick report: which groups are thriving, which are going quiet, and who stopped participating.

**Step-by-step flow:**

```
Step 1  list_chats (query="coaching", sort_by="last_active")
        --> Lists all coaching groups ranked by activity

Step 2  For each coaching group:
        get_group_activity_report (chat_jid="...", days=7)
        --> Gets: total messages, unique senders, messages/day

Step 3  For the most active group:
        get_member_engagement (chat_jid="...", days=7)
        --> Shows who's very_active, active, moderate, inactive

Step 4  For the least active group:
        get_member_engagement (chat_jid="...", days=30)
        --> Identifies members who haven't posted in a month

Step 5  AI compiles a summary:
        "Group Health Report - Week of Feb 15:
         - 6 Sisteme 2025: 142 msgs, 38 active members (HEALTHY)
         - 6 Sisteme 2024: 12 msgs, 4 active members (NEEDS ATTENTION)
         - 3 members went from active to inactive this week: ..."
```

**Business value:** The coach sees at a glance which cohorts need energy, which members are disengaging, and can act before people silently disappear. What would take hours of scrolling through groups now takes one AI query.

---

### Story 4: Cross-Group Search for Coaching Notes

**The Scenario:** The coach remembers discussing "morning routine" in some group but can't remember which one. They need to find all related discussions across all groups.

**Step-by-step flow:**

```
Step 1  cross_group_search (query="morning routine", limit=20)
        --> Searches ALL groups for "morning routine"
        --> Returns: 12 matches across 4 different groups, each
            with the message snippet, sender, date, and group name

Step 2  For the most relevant result:
        get_message_context (message_id="3A1D5011...", before=10, after=10)
        --> Shows the full conversation around that message

Step 3  The coach asks: "Now find everything about 'cold shower'"
        cross_group_search (query="cold shower", limit=10)
        --> Finds 5 more messages, some in the same groups

Step 4  AI synthesizes: "Based on discussions across 6 Sisteme 2024 and
        2025, morning routine was discussed 12 times. The most engaged
        thread was in the 2025 group on Jan 15 with 8 replies."
```

**Business value:** Global search across all WhatsApp conversations. The coach's entire coaching knowledge base -- scattered across years of group discussions -- becomes searchable in seconds. No more "I know we talked about this somewhere..."

---

### Story 5: Participant 360 View

**The Scenario:** Before a 1-on-1 coaching call with Dan, the coach wants to understand Dan's full journey: which groups he's in, how active he is, what he's been talking about.

**Step-by-step flow:**

```
Step 1  search_contacts ("Dan Luca")
        --> Finds Dan's contact info and JID

Step 2  get_participant_journey (jid="dan_luca_jid")
        --> Returns: 3 groups with messages
        --> 6 Sisteme 2024: 82 messages, last active Jan 20
        --> 6 Sisteme 2025: 51 messages, last active Feb 14
        --> VIP Coaching: 12 messages, last active Feb 12

Step 3  get_contact_groups (jid="dan_luca_jid")
        --> Shows ALL groups shared (including ones where Dan
            is silent): 15 total groups

Step 4  list_messages (chat_jid="vip_group@g.us",
                       sender_phone_number="dan_phone", limit=10)
        --> Dan's last 10 messages in the VIP group

Step 5  get_last_interaction (jid="dan_luca_jid")
        --> When was the very last time Dan messaged anywhere?

Step 6  AI compiles: "Dan Luca - Coaching Profile:
         - Active in 3 of 15 groups
         - Very active (51 msgs) in current cohort
         - Recent topics: mindset shifts, business goals
         - Engagement trend: UP compared to previous cohort"
```

**Business value:** Before every coaching call, the coach has a complete picture of the client's engagement, interests, and trajectory -- automatically compiled from real WhatsApp activity. Personalized coaching backed by data.

---

### Story 6: Community Restructuring

**The Scenario:** End of quarter. The coach wants to understand overlap between the 2024 and 2025 cohorts, decide who to move to the alumni group, and reorganize the community structure.

**Step-by-step flow:**

```
Step 1  get_group_overlap (group_jids=["cohort_2024@g.us",
                                        "cohort_2025@g.us"])
        --> Result: 61 members in both groups,
            587 only in 2024, 732 only in 2025

Step 2  get_member_engagement (chat_jid="cohort_2024@g.us", days=90)
        --> 2024 group: only 15 members still active out of 648

Step 3  get_sub_groups (jid="community_main@g.us")
        --> Lists all groups under the main community

Step 4  create_group (name="6 Sisteme Alumni", participants=[admin_jids])
        --> Creates the alumni group

Step 5  link_group (parent_jid="community@g.us",
                    child_jid="alumni_group@g.us")
        --> Adds the new group to the community

Step 6  set_group_topic (jid="alumni_group@g.us",
                         topic="Alumni community for past cohorts. Networking, events, and continued growth.")
        --> Sets the group description

Step 7  set_group_announce (jid="cohort_2024@g.us", announce=true)
        --> Locks the old group to admin-only before migration

Step 8  broadcast_to_groups (group_jids=["cohort_2024@g.us"],
                             message="This group is now archived. Join our Alumni group for continued discussions!")
        --> Sends the migration announcement
```

**Business value:** Community restructuring that normally requires hours of WhatsApp admin work -- creating groups, linking to communities, setting permissions, sending announcements -- happens through a single strategic conversation with the AI.

---

### Story 7: Event Announcement with Follow-up

**The Scenario:** The coach announces a live Q&A session, needs to track who's interested, create a time-slot poll, and react to confirmations.

**Step-by-step flow:**

```
Step 1  send_message (recipient="coaching_group@g.us",
                      message="LIVE Q&A this Saturday! Reply YES if you're in!")
        --> Sends the announcement

Step 2  (Time passes, people reply)
        list_messages (chat_jid="coaching_group@g.us", query="YES", limit=50)
        --> Finds all "YES" replies with message IDs

Step 3  For each "YES" reply:
        send_reaction (message_id="...", reaction="fire_emoji")
        --> Reacts with a fire emoji to acknowledge each confirmation

Step 4  create_poll (chat_jid="coaching_group@g.us",
                     question="What time works for the Saturday Q&A?",
                     options=["10:00 AM", "2:00 PM", "6:00 PM"],
                     max_selections=1)
        --> Creates a time-slot poll

Step 5  send_reply (quoted_message_id="original_announcement_id",
                    message="Update: Based on the poll, the Q&A is at 2 PM!
                    See you Saturday!")
        --> Replies to the original announcement with the final time

Step 6  send_status ("Live Q&A Saturday at 2 PM! DM me for the group link.")
        --> Posts to WhatsApp Status for broader visibility
```

**Business value:** The full event lifecycle -- announce, track interest, gather preferences, confirm timing, and follow up -- all orchestrated by the AI. The coach focuses on the content; the AI handles the logistics.

---

### Story 8: Status & Newsletter Automation

**The Scenario:** Daily automation: every morning, the AI posts a motivational quote to WhatsApp Status, sends it to the newsletter channel, and updates the profile status text.

**Step-by-step flow:**

```
Step 1  set_status_message ("Daily coaching insights | DM for info")
        --> Updates the "About" line under the profile name

Step 2  send_presence ("available")
        --> Goes online (so the status post is "seen" naturally)

Step 3  send_status ("Day 46/365: The only person you need to be better
        than is the person you were yesterday. -- Your coach")
        --> Posts to WhatsApp Status (visible 24h)

Step 4  get_newsletters ()
        --> Finds the "Daily Coaching Insights" channel

Step 5  newsletter_send (jid="newsletter_jid@newsletter",
                         message="Day 46 Insight: The only person you need
                         to be better than is the person you were yesterday.")
        --> Publishes to the newsletter channel

Step 6  send_presence ("unavailable")
        --> Goes back offline

Step 7  (Tomorrow, the AI does it all again with Day 47's quote)
```

**Business value:** Consistent daily presence on WhatsApp without the coach having to remember or take any manual action. The audience sees daily content on Status, the newsletter, and the profile -- all automated through one AI workflow.

---

## PART 3: ASCII Visualizations

---

### 1. Architecture Diagram

```
                          WHATSAPP MCP - HOW IT ALL CONNECTS
  ========================================================================

                    You talk to AI naturally
                              |
                              v
  ┌─────────────────────────────────────────────────────────────────────┐
  |                                                                     |
  |   "Send a motivational message to all 5 coaching groups"           |
  |                                                                     |
  |   YOUR AI ASSISTANT (Claude)                                       |
  |   Understands your intent, picks the right tools, chains them      |
  |                                                                     |
  └────────────────────────────┬────────────────────────────────────────┘
                               |
                    MCP Protocol (tool calls)
                               |
                               v
  ┌─────────────────────────────────────────────────────────────────────┐
  |                                                                     |
  |   PYTHON MCP SERVER                                                |
  |                                                                     |
  |   40 tools organized by category:                                  |
  |   - Messages, Contacts, Groups, Analytics, Newsletters...          |
  |                                                                     |
  |   Also runs SQL analytics directly on the message database         |
  |                                                                     |
  └────────────────────────────┬────────────────────────────────────────┘
                               |
                    HTTP API calls (localhost)
                               |
                               v
  ┌─────────────────────────────────────────────────────────────────────┐
  |                                                                     |
  |   GO WHATSAPP BRIDGE                                               |
  |                                                                     |
  |   - Maintains persistent connection to WhatsApp servers            |
  |   - Stores all messages in a local SQLite database                 |
  |   - Handles media (photos, videos, docs, voice notes)             |
  |   - Manages authentication (QR code login)                         |
  |                                                                     |
  └────────────────────────────┬────────────────────────────────────────┘
                               |
                    WhatsApp Web Multi-Device Protocol
                               |
                               v
  ┌─────────────────────────────────────────────────────────────────────┐
  |                                                                     |
  |   WHATSAPP SERVERS                                                 |
  |                                                                     |
  |   Your actual WhatsApp account, your groups, your contacts         |
  |   Everything happens as if YOU did it from your phone              |
  |                                                                     |
  └─────────────────────────────────────────────────────────────────────┘

  ========================================================================
   Data storage (local):
   ┌──────────────────┐  ┌──────────────────┐  ┌──────────────────┐
   |  messages.db     |  |  whatsapp.db     |  |  media/          |
   |  All chat history|  |  Session & auth  |  |  Downloaded      |
   |  + indexes       |  |  credentials     |  |  photos, files   |
   └──────────────────┘  └──────────────────┘  └──────────────────┘
```

---

### 2. Tool Category Map

```
  ========================================================================
              WHATSAPP MCP TOOL MAP - 40 TOOLS BY CATEGORY
  ========================================================================

  MESSAGING & CONVERSATIONS                 CONTACTS & SEARCH
  ┌─────────────────────────────┐           ┌─────────────────────────────┐
  | send_message                |           | search_contacts             |
  | send_file                   |           | is_on_whatsapp              |
  | send_audio_message          |           | get_contact_chats           |
  | list_messages               |           | get_contact_groups          |
  | list_chats                  |           | get_direct_chat_by_contact  |
  | get_chat                    |           | cross_group_search          |
  | get_message_context         |           └─────────────────────────────┘
  | get_last_interaction        |
  | download_media              |           REACTIONS & ENGAGEMENT
  └─────────────────────────────┘           ┌─────────────────────────────┐
                                            | send_reaction               |
  GROUPS & MANAGEMENT                       | send_reply                  |
  ┌─────────────────────────────┐           | edit_message                |
  | create_group                |           | delete_message              |
  | get_group_info              |           | mark_read                   |
  | get_group_invite_link       |           | create_poll                 |
  | set_group_name              |           └─────────────────────────────┘
  | set_group_photo             |
  | set_group_topic             |           ANALYTICS & INSIGHTS
  | set_group_announce          |           ┌─────────────────────────────┐
  | set_group_locked            |           | get_group_activity_report   |
  | set_group_join_approval     |           | get_member_engagement       |
  | join_group_with_link        |           | get_participant_journey     |
  | leave_group                 |           | get_group_overlap           |
  | update_group_participants   |           └─────────────────────────────┘
  └─────────────────────────────┘
                                            PRESENCE & PROFILE
  COMMUNITY MANAGEMENT                     ┌─────────────────────────────┐
  ┌─────────────────────────────┐           | send_presence               |
  | link_group                  |           | set_status_message          |
  | unlink_group                |           | send_status                 |
  | get_sub_groups              |           └─────────────────────────────┘
  └─────────────────────────────┘
                                            NEWSLETTERS & CHANNELS
  BULK OPERATIONS                           ┌─────────────────────────────┐
  ┌─────────────────────────────┐           | create_newsletter           |
  | broadcast_to_groups         |           | get_newsletters             |
  └─────────────────────────────┘           | newsletter_send             |
                                            └─────────────────────────────┘
```

---

### 3. User Journey Flowchart: Morning Coaching Broadcast

```
  ========================================================================
            MORNING COACHING BROADCAST - COMPLETE FLOW
  ========================================================================

  COACH SAYS:
  "Do the Monday morning broadcast to all coaching groups"
            |
            v
  ┌─────────────────────┐
  | list_chats           |
  | query="coaching"     |------> Finds 5 coaching groups
  └─────────┬───────────┘
            |
            v
  ┌─────────────────────┐         ┌──────────────────────┐
  | send_presence        |         | Simulates natural     |
  | "available"          |-------->| online behavior       |
  └─────────┬───────────┘         └──────────────────────┘
            |
            v
  ┌──────────────────────────────────────────────────────────────────┐
  | broadcast_to_groups                                              |
  |                                                                  |
  | Group 1: "6 Sisteme 2024"  -->  Message sent  (wait 3s)        |
  | Group 2: "6 Sisteme 2025"  -->  Message sent  (wait 3s)        |
  | Group 3: "6 Sisteme & 5AM" -->  Message sent  (wait 3s)        |
  | Group 4: "VIP Coaching"    -->  Message sent  (wait 3s)        |
  | Group 5: "Mindset Masters" -->  Message sent                    |
  |                                                                  |
  └─────────┬────────────────────────────────────────────────────────┘
            |
            v
  ┌──────────────────────────────────────────────────────────────────┐
  | create_poll  (x5 groups)                                         |
  |                                                                  |
  | "What's YOUR #1 goal this week?"                                 |
  | [ ] Health                                                       |
  | [ ] Business                                                     |
  | [ ] Relationships                                                |
  | [ ] Mindset                                                      |
  └─────────┬────────────────────────────────────────────────────────┘
            |
            +-----------------+-----------------+
            |                 |                 |
            v                 v                 v
  ┌──────────────┐  ┌──────────────┐  ┌──────────────────┐
  | send_status   |  | newsletter_  |  | set_status_      |
  | (WhatsApp     |  | send         |  | message          |
  |  Stories)     |  | (Channel)    |  | ("Coaching week  |
  |               |  |              |  |  starts now!")    |
  └──────┬───────┘  └──────┬───────┘  └────────┬─────────┘
         |                 |                    |
         +-----------------+--------------------+
                           |
                           v
              ┌─────────────────────┐
              | send_presence        |
              | "unavailable"        |-------> Done. Coach goes
              └─────────────────────┘          about their morning.

  ========================================================================
   RESULT: 5 groups messaged + 5 polls created + Status posted
           + Newsletter published + Profile updated
   TIME: ~30 seconds (automated) vs ~30 minutes (manual)
  ========================================================================
```

---

### 4. Engagement Dashboard Mockup

```
  ========================================================================
            WEEKLY COACHING ENGAGEMENT DASHBOARD
            Week of Feb 10-16, 2026  |  Generated by AI
  ========================================================================

  GROUP HEALTH OVERVIEW
  ─────────────────────────────────────────────────────────────────────

  6 Sisteme 2025 (793 members)
  Messages:  |||||||||||||||||||||||||||||||||||||||||||||||  287
  Senders:   ||||||||||||||||||||||||||||||                   156
  Msgs/day:  41.0    Status: THRIVING

  6 Sisteme & 5AM (648 members)
  Messages:  |||||||||||||||||||||||||||||||||                198
  Senders:   |||||||||||||||||||||                             112
  Msgs/day:  28.3    Status: HEALTHY

  VIP Coaching (45 members)
  Messages:  ||||||||||||||||||                                89
  Senders:   ||||||||||||||                                    32
  Msgs/day:  12.7    Status: HEALTHY

  Mindset Masters (320 members)
  Messages:  |||||||                                           34
  Senders:   ||||                                              18
  Msgs/day:   4.9    Status: NEEDS ATTENTION

  6 Sisteme 2024 (648 members)
  Messages:  ||                                                12
  Senders:   |                                                  4
  Msgs/day:   1.7    Status: DECLINING

  ─────────────────────────────────────────────────────────────────────

  MEMBER ENGAGEMENT BREAKDOWN (across all groups)
  ─────────────────────────────────────────────────────────────────────

  Very Active (50+ msgs)     ||||||||                 23 members
  Active (20-49 msgs)        |||||||||||||||||        67 members
  Moderate (5-19 msgs)       ||||||||||||||||||||     89 members
  Inactive (< 5 msgs)        All remaining          2,175 members

  ─────────────────────────────────────────────────────────────────────

  TOP CONTRIBUTORS THIS WEEK
  ─────────────────────────────────────────────────────────────────────

   #   Name              Groups Active    Messages   Trend
  ───  ────────────────  ──────────────   ────────   ─────
   1   Dan Luca          5/5              51         UP
   2   Maria Ionescu     3/5              38         UP
   3   Andrei Pop        4/5              29         SAME
   4   Elena Radu        2/5              24         DOWN
   5   Vlad Marin        2/5              22         NEW

  ─────────────────────────────────────────────────────────────────────

  GROUP OVERLAP ANALYSIS
  ─────────────────────────────────────────────────────────────────────

  2024 <-> 2025 cohort:   61 shared members  (9.4% overlap)
  2025 <-> VIP:           12 shared members  (VIP conversion rate: 1.5%)
  2025 <-> 5AM:          203 shared members  (25.6% cross-enrollment)

  ─────────────────────────────────────────────────────────────────────

  ALERTS
  ─────────────────────────────────────────────────────────────────────

  [!] 6 Sisteme 2024: Activity dropped 78% vs last month
      Recommendation: Archive or merge with alumni group

  [!] 14 previously "active" members went silent this week
      Top 3: Ion Barbu, Mircea Cel, Ana Stanescu

  [OK] VIP Coaching engagement UP 23% week-over-week

  ========================================================================
```

---

### 5. Weekly Coaching Workflow Timeline

```
  ========================================================================
           WEEKLY COACHING WORKFLOW - TOOL USAGE THROUGH THE WEEK
  ========================================================================

  MONDAY
  ──────────────────────────────────────────────────────────────────────

   7:00  set_status_message ............ "Coaching week starts! DM for info"
         send_presence ................. Go online
         broadcast_to_groups ........... Monday motivation to 5 groups
         create_poll (x5) .............. "What's your #1 goal this week?"
         send_status ................... Motivational quote to Stories
         newsletter_send ............... Same quote to Channel
         send_presence ................. Go offline

  TUESDAY
  ──────────────────────────────────────────────────────────────────────

   9:00  list_messages ................. Check for questions from Monday
         send_reply (x3) ............... Reply to specific questions
         send_reaction (x10) ........... React with emojis to member posts

  14:00  is_on_whatsapp ................ Verify 3 new signups
         send_message (x3) ............. Welcome DMs to new members
         send_file (x3) ................ Send onboarding PDF to each
         get_group_invite_link ......... Get invite link for cohort group

  WEDNESDAY
  ──────────────────────────────────────────────────────────────────────

  10:00  send_status ................... Mid-week insight on Stories
         newsletter_send ............... Publish coaching tip

  15:00  cross_group_search ............ "Who mentioned 'accountability'?"
         get_message_context ........... Read full conversation threads
         send_reply .................... Coach responds to key discussions

  THURSDAY
  ──────────────────────────────────────────────────────────────────────

  10:00  get_participant_journey ........ Prep for 1-on-1 coaching calls
         list_messages .................. Review client's recent messages
         get_contact_groups ............. See all shared groups

  16:00  create_poll .................... "Saturday Q&A: what topics?"
         send_message ................... Announce weekend session

  FRIDAY
  ──────────────────────────────────────────────────────────────────────

  09:00  get_group_activity_report (x5)  Weekly health check for all groups
         get_member_engagement (x5) .... Who's active, who's gone quiet
         get_group_overlap .............. Check cross-group membership

  10:00  AI compiles dashboard ......... (see mockup above)
         send_message .................. "Weekly recap" DM to coach

  14:00  set_group_announce ............ Lock one group for weekend session
         set_group_topic ............... Update with session details

  SATURDAY
  ──────────────────────────────────────────────────────────────────────

  09:00  send_status ................... "Live session at 2 PM today!"
         broadcast_to_groups ........... Reminder to all groups

  14:00  set_group_announce (false) .... Unlock group for live Q&A
         send_message .................. "We're live! Drop your questions"
         (Session happens)

  16:00  set_group_announce (true) ..... Lock group again
         create_poll ................... Session feedback poll
         send_reply .................... Thank key participants

  SUNDAY
  ──────────────────────────────────────────────────────────────────────

  10:00  send_status ................... Rest day motivation
         newsletter_send ............... Weekly summary to channel
         set_status_message ............ "Recharging. New week Monday!"

  ========================================================================
   WEEKLY TOOL USAGE SUMMARY:

   Messaging:       ~25 calls   (messages, replies, broadcasts)
   Reactions:       ~15 calls   (engagement with member posts)
   Analytics:       ~12 calls   (reports, engagement, search)
   Polls:            ~7 calls   (goals, feedback, scheduling)
   Status/Profile:   ~7 calls   (presence, stories, about text)
   Group Mgmt:       ~5 calls   (lock/unlock, topics, invites)
   Contacts:         ~5 calls   (verify, lookup, onboard)
   Newsletter:       ~4 calls   (publish to channel)
   ─────────────────────────────────────────────────────
   TOTAL:           ~80 tool calls per week
   HUMAN EFFORT:    ~10 minutes of AI conversation per day
  ========================================================================
```

---

## Appendix: Quick Reference

### How to get started
1. The Go bridge connects to your WhatsApp account (one-time QR code scan)
2. The Python MCP server exposes all tools to your AI assistant
3. You talk to the AI in natural language -- it picks the right tools automatically

### Limits to be aware of
- WhatsApp rate limits apply (the broadcast tool has built-in delays)
- Media files must be downloaded explicitly (not stored automatically)
- The bridge needs to be running for real-time actions
- Analytics tools work on locally stored message history
- Profile status text maxes out at 139 characters
- WhatsApp Status posts are visible for 24 hours

### What this does NOT do (yet)
- Read poll results (can create polls, but can't read votes)
- Post image/video to WhatsApp Status (text only for now)
- Delete newsletters
- Create WhatsApp Communities (can manage existing ones)
- Schedule messages for future delivery (the AI acts in real-time)

---

*Report generated February 2026. Based on 40 tested MCP tools running on the `variant-data-folder-in-mcp-server` branch.*
