-- backfill_chat_names.sql
--
-- Repairs already-corrupted 1:1 @lid chat names in messages.db.
--
-- BACKGROUND
-- ----------
-- Before the GetChatName fix, a brand-new @lid chat with no contact name stored
-- got its `chats.name` set to the message `sender`. For OUTGOING messages the
-- sender is the OWNER's own LID (e.g. 169440771625138), so the other party's
-- chat name was overwritten with the owner's number. For INCOMING messages it
-- got the contact's own bare LID. Either way `chats.name` became a bare number.
--
-- The real name usually already exists on the corresponding phone-number (PN)
-- chat row, reachable via the jid_mappings table (lid_jid -> pn_jid).
--
-- WHAT THIS SCRIPT DOES
-- ---------------------
-- For every individual @lid chat whose name is bare-numeric (no letters) AND
-- whose mapped PN chat has a real (letter-bearing) name, copy that real name
-- onto the @lid chat row. Rows without a resolvable real name are left as-is.
--
-- "Real name" predicate: GLOB '*[A-Za-z]*' (contains at least one ASCII letter).
-- This mirrors the Go isRealName() helper. Names such as "Cosmin Țambrea" match
-- because they still contain ASCII letters; purely non-ASCII names would not be
-- matched by this ASCII approximation (none observed in this DB).
--
-- HOW TO RUN (manual, read the preview first)
-- -------------------------------------------
--   DB=/Users/cristi/CLAUDE/whatsapp-media/messages.db
--   sqlite3 "$DB" < whatsapp-bridge/backfill_chat_names.sql   # runs PREVIEW + UPDATE
-- To inspect only, comment out the BEGIN..COMMIT block, or run the PREVIEW
-- query alone first. Take a backup before mutating a live DB:
--   cp "$DB" "$DB.bak-$(date +%Y%m%d-%H%M%S)"

----------------------------------------------------------------------
-- 1) PREVIEW (read-only): rows that WILL be updated, with old/new name
----------------------------------------------------------------------
SELECT
    c.jid              AS lid_jid,
    c.name             AS current_corrupt_name,
    m.pn_jid           AS mapped_pn_jid,
    p.name             AS new_name
FROM chats c
JOIN jid_mappings m ON m.lid_jid = c.jid
JOIN chats        p ON p.jid    = m.pn_jid
WHERE c.jid LIKE '%@lid'
  AND c.name NOT GLOB '*[A-Za-z]*'      -- current name is bare-numeric (no letters)
  AND p.name      GLOB '*[A-Za-z]*'     -- mapped PN chat has a real name
ORDER BY c.name = '169440771625138' DESC, p.name;   -- owner-LID-corrupted rows first

----------------------------------------------------------------------
-- 2) UPDATE: apply the fix (wrapped in a transaction)
--    Portable correlated-subquery form (no UPDATE..FROM dependency).
----------------------------------------------------------------------
BEGIN TRANSACTION;

UPDATE chats
SET name = (
    SELECT p.name
    FROM jid_mappings m
    JOIN chats p ON p.jid = m.pn_jid
    WHERE m.lid_jid = chats.jid
      AND p.name GLOB '*[A-Za-z]*'
)
WHERE chats.jid LIKE '%@lid'
  AND chats.name NOT GLOB '*[A-Za-z]*'
  AND EXISTS (
      SELECT 1
      FROM jid_mappings m
      JOIN chats p ON p.jid = m.pn_jid
      WHERE m.lid_jid = chats.jid
        AND p.name GLOB '*[A-Za-z]*'
  );

COMMIT;

----------------------------------------------------------------------
-- 3) VERIFY (read-only): should report 0 remaining resolvable-but-corrupt rows
----------------------------------------------------------------------
SELECT COUNT(*) AS still_corrupt_but_resolvable
FROM chats c
JOIN jid_mappings m ON m.lid_jid = c.jid
JOIN chats        p ON p.jid    = m.pn_jid
WHERE c.jid LIKE '%@lid'
  AND c.name NOT GLOB '*[A-Za-z]*'
  AND p.name      GLOB '*[A-Za-z]*';

----------------------------------------------------------------------
-- OPTIONAL (commented out): for the remaining bare-LID chats that have a
-- jid_mappings entry but NO real PN name yet, upgrade the bare LID name to the
-- mapped phone number (still better than a LID). Uncomment to apply.
----------------------------------------------------------------------
-- BEGIN TRANSACTION;
-- UPDATE chats
-- SET name = (
--     SELECT replace(m.pn_jid, '@s.whatsapp.net', '')
--     FROM jid_mappings m
--     WHERE m.lid_jid = chats.jid
-- )
-- WHERE chats.jid LIKE '%@lid'
--   AND chats.name NOT GLOB '*[A-Za-z]*'
--   AND EXISTS (SELECT 1 FROM jid_mappings m WHERE m.lid_jid = chats.jid)
--   AND NOT EXISTS (
--       SELECT 1 FROM jid_mappings m JOIN chats p ON p.jid = m.pn_jid
--       WHERE m.lid_jid = chats.jid AND p.name GLOB '*[A-Za-z]*'
--   );
-- COMMIT;
