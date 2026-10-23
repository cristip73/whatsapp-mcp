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
        whatsapp._phone_reached_bridge = False
        self.bridge = FakeBridge().__enter__()
        whatsapp.WHATSAPP_API_BASE_URL = self.bridge.base

    def tearDown(self):
        self.bridge.__exit__(None, None, None)
        whatsapp.WHATSAPP_API_BASE_URL = self.old_base
        whatsapp._new_codes_by_phone.clear()
        whatsapp._phone_reached_bridge = False

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

    # --- qr -------------------------------------------------------------------

    def test_qr_new_bridge_passes_fields_and_guidance(self):
        self.bridge.responses["/api/qr"] = (200, {
            "success": True, "qr": "2@abc,def", "image_path": "/tmp/wa-qr/current.png",
            "text_qr": "#### QR ####", "expires_in_sec": 58, "refs_left": 5, "message": "qr ready",
        })
        out = whatsapp.qr()
        self.assertTrue(out["success"])
        self.assertEqual(out["image_path"], "/tmp/wa-qr/current.png")
        self.assertEqual(out["markdown"], "![QR](/tmp/wa-qr/current.png)")
        self.assertEqual(out["expires_in_sec"], 58)
        self.assertEqual(out["refs_left"], 5)
        self.assertEqual(out["text_qr"], "#### QR ####")
        self.assertNotIn("qr", out)  # raw ref string is not useful to the agent
        self.assertIn("absolute path", out["guidance"])
        self.assertIn("code block", out["guidance"])
        self.assertIn("call action='qr' again", out["guidance"])
        self.assertIn("logged_in", out["guidance"])
        self.assertIn("Do NOT choose", out["phone_steps"])
        method, path, _ = self.bridge.requests[-1]
        self.assertEqual((method, path), ("POST", "/api/qr"))

    def test_qr_guidance_requires_another_screen_via_t3_web(self):
        self.bridge.responses["/api/qr"] = (200, {
            "success": True, "image_path": "/tmp/wa-qr/current.png", "text_qr": "x",
            "expires_in_sec": 60, "refs_left": 6,
        })
        guidance = whatsapp.qr()["guidance"]
        self.assertIn("https://app.t3.codes/", guidance)
        self.assertIn("DIFFERENT screen", guidance)
        self.assertIn("your T3 password", guidance)
        self.assertIn("after they confirm", guidance)

    def test_qr_old_bridge_404_points_to_pair(self):
        # no /api/qr route on the fake bridge -> 404, like a bridge from before the QR API
        out = whatsapp.qr()
        self.assertFalse(out["success"])
        self.assertIs(out["qr_supported"], False)
        self.assertIn("action='pair'", out["message"])

    def test_qr_failure_already_linked(self):
        self.bridge.responses["/api/qr"] = (409, {"success": False, "message": "already linked; nothing to pair"})
        out = whatsapp.qr()
        self.assertFalse(out["success"])
        self.assertIn("Already linked", out["next_step"])

    def test_status_qr_shown_passes_fields_and_hint(self):
        pairing = {"state": "qr_shown", "qr_expires_in_sec": 15, "refs_left": 3,
                   "last_event": "qr shown", "last_event_age_sec": 5}
        self.bridge.responses["/api/status"] = (200, {
            "connected": True, "logged_in": False, "own_jid": "", "pairing": pairing,
        })
        out = whatsapp.connection_status()
        self.assertEqual(out["pairing"], pairing)
        self.assertIn("QR is on screen", out["hint"])

    def test_phone_reached_bridge_fallback_on_last_event(self):
        # bridge from 23 Oct morning: no phone_reached_bridge field, only last_event
        self.bridge.responses["/api/status"] = (200, {
            "connected": True, "logged_in": False, "own_jid": "",
            "pairing": {"state": "idle", "code_age_sec": None, "last_event": "notification received",
                        "last_event_age_sec": 3},
        })
        status = whatsapp.connection_status()
        self.assertIn("action='qr'", status["hint"])
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "WXYZ-1234", "reused": False, "age_sec": 0, "expires_in_sec": 160,
        })
        out = whatsapp.pair("40700000000")
        self.assertIn("action='qr'", out["warning"])

    def test_phone_reached_bridge_field_steers_to_qr(self):
        # new bridge: explicit field, last_event already overwritten by a later event
        self.bridge.responses["/api/status"] = (200, {
            "connected": True, "logged_in": False, "own_jid": "",
            "pairing": {"state": "idle", "phone_reached_bridge": True,
                        "last_event": "login socket closed by server after 162s", "last_event_age_sec": 2},
        })
        self.assertIn("action='qr'", whatsapp.connection_status()["hint"])
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "WXYZ-1234", "reused": False, "age_sec": 0, "expires_in_sec": 160,
        })
        self.assertIn("action='qr'", whatsapp.pair("40700000000")["warning"])

    def test_phone_reached_bridge_false_wins_over_last_event(self):
        self.bridge.responses["/api/status"] = (200, {
            "connected": True, "logged_in": False, "own_jid": "",
            "pairing": {"state": "idle", "phone_reached_bridge": False,
                        "last_event": "notification received", "last_event_age_sec": 2},
        })
        self.assertNotIn("reached this bridge", whatsapp.connection_status()["hint"])
        self.assertFalse(whatsapp._phone_reached_bridge)

    def test_pair_guidance_recommends_qr_and_switch_rule(self):
        self.bridge.responses["/api/pair"] = (200, {
            "success": True, "code": "ABCD-EFGH", "reused": False, "age_sec": 0, "expires_in_sec": 160,
        })
        out = whatsapp.pair("40700000000")
        self.assertIn("action='qr' is the recommended way", out["guidance"])
        self.assertIn("notification received", out["guidance"])


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
