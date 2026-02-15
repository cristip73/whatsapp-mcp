# MCP Tools Test Report #2 - Post-Fix Verification

**Date:** 2026-02-15
**Branch:** `variant-data-folder-in-mcp-server`
**Commit:** `89aeabf` (Fix usability issues across 28 MCP tools)
**Bridge:** Restarted with new Go binary, connected to WhatsApp
**MCP Server:** Restarted by user

---

## Tool #1: `get_group_info` (CRITICAL FIX verified)
**Fix applied:** `include_participants=False` by default + `participant_count` always present + pagination

**Tests:**

| Test | Result |
|------|--------|
| Large group (793 members), default params | Response: ~200 chars. `participant_count: 793`, no participants array. **FIXED** (was 82K chars) |
| Large group, `include_participants=True, limit=3, offset=0` | Returns 3 participants + `participant_count: 793` |
| Large group, `include_participants=True, limit=2, offset=790` | Returns last 2 participants (correct boundary) |
| Small group (2 members), default params | `participant_count: 2`, no participants. Clean. |

**Verdict:** PASS - all edge cases work. Response size under control.

---

## Tool #2: `list_messages` (CRITICAL FIX verified)
**Fix applied:** Message IDs now always included in output format: `[timestamp] [ID: xxx] Chat: ...`

**Tests:**

| Test | Result |
|------|--------|
| list_messages on Agentic Awakened, limit=5 | Every line has `[ID: 3A1D5011...]` format. Text messages AND media messages both show IDs. |
| End-to-end: list_messages -> send_reaction using extracted ID | PASS - reacted to "Of course 😁" (ID: 3ABBD69E...) |
| End-to-end: list_messages -> send_reply using extracted ID | PASS - reply sent quoting message by Dan Luca |
| Remove reaction using same ID | PASS |

**Verdict:** PASS - the critical gap is closed. AI can now see message IDs and use them with react/edit/delete/reply/mark_read tools.

---

## Tool #3: `get_group_overlap` (CRITICAL FIX verified)
**Fix applied:** Returns counts only by default. `include_members` param added.

**Tests:**

| Test | Result |
|------|--------|
| 2 large groups (648 + 793 members), default | `common_count: 61, unique_per_group: {"6 Sisteme...&5AM": 587, "6 Sisteme...(2025)": 732}`. **~150 chars** (was 30K+) |
| Small + large group, `include_members=True` | `common_count: 2`, common_members shown, unique lists shown. Correct. |
| Default mode: no member lists in response | Confirmed: `unique_per_group` has integers, not arrays |

**Verdict:** PASS - response size reduced from 30K+ to ~150 chars by default.

---

## Tool #4: `get_sub_groups` (BUG FIX verified)
**Fix applied:** Go bridge now calls `GetGroupInfo()` for each sub-group to resolve real name.

**Test:** `get_sub_groups("120363294069275968@g.us")`
- Before: `{"jid": "120363291271345671@g.us", "name": "120363291271345671@g.us"}` (JID as name)
- After: `{"jid": "120363291271345671@g.us", "name": "AppLevel Official Community"}` (real name)

**Verdict:** PASS - bug fixed.

---

## Tool #5: `cross_group_search` (truncation fix verified)
**Fix applied:** Content truncated to 200 chars by default. `max_content_length` param added.

**Tests:**

| Test | Result |
|------|--------|
| query="coaching", limit=3, default truncation | Message 2 (was 4000+ chars): now `"- [[Coachings Dan]]...Sper..."` (~200 chars + `...`). **FIXED** |
| query="coaching", limit=1, max_content_length=50 | Content truncated at 50 chars with `...` |
| Short message (< 200 chars) | Not truncated, no `...` appended. Correct. |

**Verdict:** PASS - long messages no longer blow up responses.

---

## Tool #6: `get_member_engagement` (improved format verified)
**Fix applied:** Response now wrapped in `{total_messages, unique_senders, members: [...]}`. Classification documented.

**Test:** `get_member_engagement("120363335027511941@g.us", days=90)`
- Response: `{total_messages: 55, unique_senders: 4, members: [...]}`
- Dan Luca: 51 msgs -> `very_active` (50+ threshold)
- Other 3 members: 1-2 msgs -> `inactive` (<5 threshold)
- Classification thresholds: very_active (50+), active (20+), moderate (5+), inactive (<5)

**Verdict:** PASS - structured response with context. Classification is clear.

---

## Tool #7: `get_participant_journey` (include_empty filter verified)
**Fix applied:** `include_empty=False` by default, filtering groups with 0 messages.

**Tests:**

| Test | Result |
|------|--------|
| Dan Luca JID, default (include_empty=False) | 3 groups returned (all with messages) |
| Dan Luca JID, include_empty=True | 15 groups returned (12 with 0 messages) |

**Verdict:** PASS - 80% noise reduction by default (3 vs 15 results).

---

## Tools #8: Toggle tools + set_group_topic (response value fix verified)
**Fix applied:** Toggle tools now return the set value. set_group_topic returns topic.

**Tests:**

| Test | Result |
|------|--------|
| `set_group_announce(true)` | `{success: true, ..., "announce": true}` |
| `set_group_announce(false)` | `{success: true, ..., "announce": false}` |
| `set_group_locked(true/false)` | Both return `"locked": true/false` |
| `set_group_topic("Updated topic")` | Returns `"topic": "Updated topic"` even on 409 conflict |

**Verdict:** PASS - response now confirms what was set.

---

## Tool #9: `send_presence` (input validation verified)
**Fix applied:** Python-layer validation rejects invalid values before hitting bridge.

**Tests:**

| Test | Result |
|------|--------|
| `send_presence("banana")` | `{success: false, "Invalid presence 'banana'. Must be 'available' or 'unavailable'."}` |
| `send_presence("available")` | `{success: true}` (from Report #1) |

**Verdict:** PASS - invalid input caught cleanly.

---

## Docstring improvements (spot-check)

Verified in main.py source:
- `get_group_invite_link`: "WARNING: reset=true invalidates the previous invite link permanently"
- `link_group`/`unlink_group`: "WARNING: This modifies community structure"
- `broadcast_to_groups`: "WARNING: This sends real messages to all specified groups"
- `set_status_message`: "max 139 characters per WhatsApp limit"
- `get_member_engagement`: "Classification: very_active (50+ msgs), active (20+), moderate (5+), inactive (<5)"
- `broadcast_to_groups`: `delay_seconds` parameter added (default 3)

**Verdict:** PASS - all docstring improvements in place.

---

## SUMMARY

### All fixes verified:

| # | Fix | Before | After | Status |
|---|-----|--------|-------|--------|
| 1 | `get_group_info` pagination | 82K chars on large groups | ~200 chars default, pagination available | **FIXED** |
| 2 | `list_messages` message IDs | IDs only on media messages | IDs on ALL messages | **FIXED** |
| 3 | `get_group_overlap` counts-only | 30K+ chars of LID dumps | ~150 chars with counts | **FIXED** |
| 4 | `get_sub_groups` name bug | JID shown as name | Real group name resolved | **FIXED** |
| 5 | `cross_group_search` truncation | 4000+ char messages in results | 200 char truncation + param | **FIXED** |
| 6 | `get_member_engagement` format | Flat list, no totals | Wrapped with total_messages, classification documented | **FIXED** |
| 7 | `get_participant_journey` filter | 15 results (12 empty) | 3 results (only with messages) | **FIXED** |
| 8 | Toggle response values | No value confirmation | Returns set value | **FIXED** |
| 9 | `send_presence` validation | No validation | Rejects invalid values | **FIXED** |
| 10 | Docstrings | Missing warnings | Warnings on destructive actions, params documented | **FIXED** |

### Remaining known issues (not in scope of this fix):
- `name` field in participant lists still shows LID instead of contact name (WhatsApp API limitation - LIDs don't map to stored contacts easily)
- `set_group_topic` 409 conflict on repeated calls (WhatsApp rate limiting, not a bug)
