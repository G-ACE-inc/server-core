"""Offline hermetic Telegram ingress and fail-closed egress contract tests.
No real network, credentials, Cloudflare or Telegram services are contacted.
"""
import hmac
import unittest

HEADER = "X-Telegram-Bot-Api-Secret-Token"

class WebhookBoundary:
    def __init__(self, secret):
        self.secret = secret

    def authorize(self, path, method, headers):
        supplied = headers.get(HEADER, "")
        return (path == "/telegram/webhook" and method == "POST"
                and isinstance(supplied, str)
                and hmac.compare_digest(supplied.encode(), self.secret.encode()))

class FailClosedEgress:
    """Routing-policy model only, NOT kernel firewall or real VPN."""
    def __init__(self, proxy):
        self.proxy = proxy
        self.calls = []

    def send(self, host, payload):
        if host != "api.telegram.org":
            raise PermissionError("destination denied")
        if self.proxy is None or not self.proxy.connected:
            raise ConnectionError("egress unavailable: no direct fallback")
        self.calls.append(("via_proxy", host, len(payload)))
        return self.proxy.forward(host, payload)

class FakeProxy:
    def __init__(self):
        self.connected = True
        self.forwarded = []

    def forward(self, host, payload):
        self.forwarded.append((host, payload))
        return b"OK"

class BoundaryTests(unittest.TestCase):
    def setUp(self):
        self.boundary = WebhookBoundary("test-secret-only")
        self.proxy = FakeProxy()
        self.egress = FailClosedEgress(self.proxy)

    def test_valid_webhook(self):
        self.assertTrue(self.boundary.authorize("/telegram/webhook", "POST", {HEADER: "test-secret-only"}))

    def test_reject_missing_secret(self):
        self.assertFalse(self.boundary.authorize("/telegram/webhook", "POST", {}))

    def test_reject_wrong_secret(self):
        self.assertFalse(self.boundary.authorize("/telegram/webhook", "POST", {HEADER: "bad"}))

    def test_reject_wrong_method_and_path(self):
        self.assertFalse(self.boundary.authorize("/telegram/webhook", "GET", {HEADER: "test-secret-only"}))
        self.assertFalse(self.boundary.authorize("/admin", "POST", {HEADER: "test-secret-only"}))

    def test_forward_via_proxy(self):
        self.assertEqual(self.egress.send("api.telegram.org", b"hello"), b"OK")
        self.assertEqual(self.proxy.forwarded, [("api.telegram.org", b"hello")])

    def test_proxy_down_is_fail_closed(self):
        self.proxy.connected = False
        with self.assertRaises(ConnectionError):
            self.egress.send("api.telegram.org", b"hello")
        self.assertEqual(self.egress.calls, [])
        self.assertEqual(self.proxy.forwarded, [])

    def test_unapproved_destination(self):
        with self.assertRaises(PermissionError):
            self.egress.send("example.org", b"hello")
        self.assertEqual(self.proxy.forwarded, [])

    def test_missing_proxy_is_fail_closed(self):
        self.egress.proxy = None
        with self.assertRaises(ConnectionError):
            self.egress.send("api.telegram.org", b"hello")

if __name__ == "__main__":
    unittest.main(verbosity=2)
