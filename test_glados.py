import unittest
import json
import re

# We will test extract_cookie, get_session_cookie_kind, get_browser_headers, parse_checkin
from glados import extract_cookie, get_session_cookie_kind, get_browser_headers

class TestGlados(unittest.TestCase):
    def test_extract_cookie_standard(self):
        c = "gld:sess=abc; gld:sess.sig=xyz"
        self.assertEqual(extract_cookie(c), c)

    def test_extract_cookie_prefix(self):
        c = "Cookie: gld:sess=abc; gld:sess.sig=xyz"
        self.assertEqual(extract_cookie(c), "gld:sess=abc; gld:sess.sig=xyz")

    def test_extract_cookie_json_editor(self):
        json_data = json.dumps([
            {"name": "gld:sess", "value": "abc"},
            {"name": "gld:sess.sig", "value": "xyz"}
        ])
        extracted = extract_cookie(json_data)
        self.assertIn("gld:sess=abc", extracted)
        self.assertIn("gld:sess.sig=xyz", extracted)

    def test_session_cookie_kind(self):
        self.assertEqual(get_session_cookie_kind("gld:sess=abc; gld:sess.sig=xyz"), "gld")
        self.assertEqual(get_session_cookie_kind("koa:sess=abc; koa:sess.sig=xyz"), "koa")
        self.assertIsNone(get_session_cookie_kind("other=123"))

    def test_browser_headers_default(self):
        h = get_browser_headers()
        self.assertIn("User-Agent", h)
        self.assertIn("Sec-CH-UA", h)
        self.assertEqual(h["Sec-CH-UA-Platform"], '"Windows"')

    def test_browser_headers_mac(self):
        mac_ua = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
        h = get_browser_headers(mac_ua)
        self.assertEqual(h["User-Agent"], mac_ua)
        self.assertEqual(h["Sec-CH-UA-Platform"], '"macOS"')
        self.assertIn('"Chromium";v="128"', h["Sec-CH-UA"])

    def test_client_status_and_checkin_parsing(self):
        from unittest.mock import patch, MagicMock
        from glados import GLaDOSClient

        client = GLaDOSClient("gld:sess=abc; gld:sess.sig=xyz")
        with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
            # Mock status
            mock_status_resp = MagicMock()
            mock_status_resp.status_code = 200
            mock_status_resp.json.return_value = {
                "code": 0,
                "data": {"email": "test@example.com", "leftDays": "120.5"}
            }
            mock_get.return_value = mock_status_resp

            client.get_status()
            self.assertEqual(client.email, "test@example.com")
            self.assertEqual(client.left_days, "120")

            # Mock checkin
            mock_checkin_resp = MagicMock()
            mock_checkin_resp.status_code = 200
            mock_checkin_resp.json.return_value = {
                "code": 0,
                "message": "Today's observation logged. Return tomorrow for more points.",
                "list": [{"change": "2", "balance": "50"}]
            }
            mock_post.return_value = mock_checkin_resp

            res = client.checkin()
            self.assertEqual(res["code"], 0)
            self.assertIn("observation", res["message"])

if __name__ == '__main__':
    unittest.main()
