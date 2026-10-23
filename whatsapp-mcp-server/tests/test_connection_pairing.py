"""connection tool: what the agent sees on status / pair / reconnect.

Uses a real local HTTP server as a fake bridge (no WhatsApp, no real numbers).
"""
import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer

import whatsapp


class FakeBridge:
    """Serves canned JSON per path; records the requests it got."""

    def __init__(self):
        self.responses = {}  # path -> (status, body)
        self.requests = []
        bridge = self

        class Handler(BaseHTTPRequestHandler):
            def _reply(self):
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                bridge.requests.append((self.command, self.path, body))
                status, payload = bridge.responses.get(self.path, (404, {"error": "no route"}))
                data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            do_GET = _reply
            do_POST = _reply

            def log_message(self, *args):
                pass

        self.server = HTTPServer(("127.0.0.1", 0), Handler)
        self.thread = threading.Thread(target=self.server.serve_forever, daemon=True)

    def __enter__(self):
        self.thread.start()
        return self

    def __exit__(self, *exc):
        self.server.shutdown()
        self.server.server_close()

    @property
    def base(self):
        return f"http://127.0.0.1:{self.server.server_address[1]}/api"


class PairingTests(unittest.TestCase):
    def setUp(self):
        self.old_base = whatsapp.WHATSAPP_API_BASE_URL
        whatsapp._new_codes_by_phone.clear()
        self.bridge = FakeBridge().__enter__()
        whatsapp.WHATSAPP_API_BASE_URL = self.bridge.base

    def tearDown(self):
        self.bridge.__exit__(None, None, None)
        whatsapp.WHATSAPP_API_BASE_URL = self.old_base
        whatsapp._new_codes_by_phone.clear()

    # --- pair, new bridge ---------------------------------------------------

    def test_pair_new_bridge_passes_contract_fields_and_guidance(self):
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "ABCD-EFGH", "reused": False, "age_sec": 0,
            "expires_in_sec": 160, "message": "code issued",
        })
        out = whatsapp.pair("40700000000")
        self.assertTrue(out["success"])
        self.assertEqual(out["code"], "ABCD-EFGH")
        self.assertIs(out["reused"], False)
        self.assertEqual(out["age_sec"], 0)
        self.assertEqual(out["expires_in_sec"], 160)
        self.assertIn("do not call pair for that", out["guidance"])
        self.assertIn("same number", out["guidance"])
        self.assertIn("A new code cancels the previous one", out["guidance"])
        self.assertIn("4 linked devices", out["guidance"])
        self.assertIn("few hours", out["guidance"])
        self.assertIn("Link with phone number instead", out["phone_steps"])
        self.assertEqual(out["new_codes_last_hour"], 1)
        self.assertNotIn("warning", out)
        method, path, body = self.bridge.requests[-1]
        self.assertEqual((method, path), ("POST", "/api/pair"))
        self.assertEqual(json.loads(body), {"phone": "40700000000"})

    def test_pair_reused_code_is_not_counted_as_new(self):
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "ABCD-EFGH", "reused": False, "age_sec": 0, "expires_in_sec": 160,
        })
        whatsapp.pair("40700000000")
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "ABCD-EFGH", "reused": True, "age_sec": 40, "expires_in_sec": 120,
        })
        out = whatsapp.pair("40700000000")
        self.assertIs(out["reused"], True)
        self.assertEqual(out["age_sec"], 40)
        self.assertEqual(out["expires_in_sec"], 120)
        self.assertNotIn("new_codes_last_hour", out)
        self.assertEqual(len(whatsapp._new_codes_by_phone["40700000000"]), 1)

    def test_third_new_code_in_an_hour_carries_stop_warning(self):
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "AAAA-BBBB", "reused": False, "age_sec": 0, "expires_in_sec": 160,
        })
        first = whatsapp.pair("40700000000")
        second = whatsapp.pair("40700000000")
        third = whatsapp.pair("+40 700 000 000")  # same digits, other formatting
        self.assertNotIn("warning", first)
        self.assertNotIn("warning", second)
        self.assertEqual(third["new_codes_last_hour"], 3)
        self.assertIn("STOP", third["warning"])
        self.assertIn("few hours", third["warning"])

    # --- pair, old bridge (before the reuse contract) -------------------------

    def test_pair_old_bridge_drops_fixed_expiry_and_does_not_crash(self):
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "ABCD-EFGH", "expires_in_sec": 150,
            "instructions": "On the phone: ...",
        })
        out = whatsapp.pair("40700000000")
        self.assertTrue(out["success"])
        self.assertEqual(out["code"], "ABCD-EFGH")
        self.assertIsNone(out["expires_in_sec"])
        self.assertNotIn("reused", out)
        self.assertNotIn("instructions", out)
        self.assertIn("NEW code", out["guidance"])
        self.assertIn("show this same code again", out["guidance"])

    def test_pair_failure_passes_message_and_next_step(self):
        self.bridge.responses["/api/pair"] = (503, {
            "success": False, "message": "bridge is restarting after a logout; try again in about a minute",
        })
        out = whatsapp.pair("40700000000")
        self.assertFalse(out["success"])
        self.assertIn("restarting", out["message"])
        self.assertIn("about a minute", out["next_step"])

    def test_pair_non_json_answer(self):
        self.bridge.responses["/api/pair"] = (502, b"<html>bad gateway</html>")
        out = whatsapp.pair("40700000000")
        self.assertFalse(out["success"])
        self.assertIn("HTTP 502", out["message"])

    def test_pair_bridge_unreachable(self):
        whatsapp.WHATSAPP_API_BASE_URL = "http://127.0.0.1:9/api"
        out = whatsapp.pair("40700000000")
        self.assertFalse(out["success"])
        self.assertIn("Bridge unreachable", out["message"])

    # --- status ---------------------------------------------------------------

    def test_status_passes_pairing_object_and_hint(self):
        pairing = {"state": "code_issued", "code_age_sec": 30, "last_event": "code issued", "last_event_age_sec": 30}
        self.bridge.responses["/api/status"] = (200, {
            "connected": True, "logged_in": False, "own_jid": "", "pairing": pairing,
        })
        out = whatsapp.connection_status()
        self.assertEqual(out["pairing"], pairing)
        self.assertIn("show the code you already gave", out["hint"])

    def test_status_old_bridge_without_pairing(self):
        self.bridge.responses["/api/status"] = (200, {"connected": False, "logged_in": False, "own_jid": ""})
        out = whatsapp.connection_status()
        self.assertNotIn("pairing", out)
        self.assertIn("call pair once", out["hint"])

    def test_status_linked_has_no_hint(self):
        self.bridge.responses["/api/status"] = (200, {"connected": True, "logged_in": True, "own_jid": "x"})
        self.assertNotIn("hint", whatsapp.connection_status())

    # --- reconnect --------------------------------------------------------------

    def test_reconnect_on_unlinked_bridge_points_to_pair(self):
        self.bridge.responses["/api/reconnect"] = (500, {
            "success": False, "message": "not logged in - restart bridge and scan QR code",
        })
        out = whatsapp.reconnect()
        self.assertFalse(out["success"])
        self.assertIn("action='pair'", out["message"])
        self.assertNotIn("scan QR", out["message"])

    def test_reconnect_failure_checks_status_when_message_is_unknown(self):
        self.bridge.responses["/api/reconnect"] = (500, {"success": False, "message": "something else"})
        self.bridge.responses["/api/status"] = (200, {"connected": False, "logged_in": False, "own_jid": ""})
        out = whatsapp.reconnect()
        self.assertIn("action='pair'", out["message"])

    def test_reconnect_success_passes_through(self):
        self.bridge.responses["/api/reconnect"] = (200, {"success": True, "message": "already connected"})
        self.assertEqual(whatsapp.reconnect(), {"success": True, "message": "already connected"})


if __name__ == "__main__":
    unittest.main()
