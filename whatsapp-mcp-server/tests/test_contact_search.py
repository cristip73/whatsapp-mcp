import os
import sqlite3
import tempfile
import unittest

import whatsapp


class ContactSearchTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        whatsapp.initialize_attachments_path(self.temp_dir.name)

        db_path = os.path.join(self.temp_dir.name, "messages.db")
        conn = sqlite3.connect(db_path)
        try:
            conn.execute("CREATE TABLE chats (jid TEXT PRIMARY KEY, name TEXT, last_message_time TEXT)")
            conn.executemany(
                "INSERT INTO chats (jid, name, last_message_time) VALUES (?, ?, ?)",
                [
                    ("40711111111@s.whatsapp.net", "Ioana Ivănoiu", None),
                    ("40722222222@s.whatsapp.net", "Stefan Toma", None),
                    ("120363000000000000@g.us", "Ioana Ivănoiu Group", None),
                ],
            )
            conn.commit()
        finally:
            conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_query_without_diacritics_matches_stored_name_with_diacritics(self):
        contacts = whatsapp.search_contacts("Ioana Ivanoiu")

        self.assertEqual([contact.name for contact in contacts], ["Ioana Ivănoiu"])

    def test_query_with_diacritics_matches_stored_name_without_diacritics(self):
        contacts = whatsapp.search_contacts("Ștefan Țoma")

        self.assertEqual([contact.name for contact in contacts], ["Stefan Toma"])


if __name__ == "__main__":
    unittest.main()
