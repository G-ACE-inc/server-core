import importlib.util
from pathlib import Path
import unittest


MODULE = Path(__file__).resolve().parents[1] / "scripts/chat_host_commit_status.py"
spec = importlib.util.spec_from_file_location("chat_host_commit_status", MODULE)
status = importlib.util.module_from_spec(spec)
spec.loader.exec_module(status)
REQUEST_ID = "req_" + "a" * 24
COMMIT = "b" * 40
RUN = "42666161316"
RESULT = "https://github.com/G-ACE-inc/server-core/issues/10#issuecomment-6746980214"


class CommitStatusLocatorTests(unittest.TestCase):
    def test_verified_host_result_is_discoverable_without_private_output(self):
        observation = {
            "request_id": REQUEST_ID, "result_verified": True, "state": "PASS",
            "exit_code": 0, "result_url": RESULT,
            "streams": {"stdout": {"bytes": 213}}, "stdout": "secret output",
        }
        payload = status.status_payload(REQUEST_ID, COMMIT, RUN, observation)
        self.assertEqual(payload["state"], "success")
        self.assertEqual(payload["target_url"],
                         f"https://github.com/G-ACE-inc/server-core/actions/runs/{RUN}")
        self.assertIn(REQUEST_ID, payload["description"])
        self.assertIn(RUN, payload["description"])
        self.assertNotIn("secret output", str(payload))
        self.assertNotIn(RESULT, str(payload))

    def test_missing_or_mismatched_result_is_not_reported_as_pass(self):
        for observation in (None, {"request_id": "req_" + "c" * 24,
                                   "result_verified": True, "state": "PASS", "exit_code": 0},
                            {"request_id": REQUEST_ID, "result_verified": False,
                             "state": "PASS", "exit_code": 0}):
            with self.subTest(observation=observation):
                payload = status.status_payload(REQUEST_ID, COMMIT, RUN, observation)
                self.assertEqual(payload["state"], "error")
                self.assertIn("/actions/runs/", payload["target_url"])

    def test_host_failure_and_untrusted_url(self):
        payload = status.status_payload(REQUEST_ID, COMMIT, RUN, {
            "request_id": REQUEST_ID, "result_verified": True, "state": "FAIL",
            "exit_code": 1, "result_url": "https://example.net/private",
        })
        self.assertEqual(payload["state"], "failure")
        self.assertNotIn("example.net", str(payload))

    def test_rejects_invalid_identifier(self):
        for request_id, sha, run in (("req_short", COMMIT, RUN),
                                     (REQUEST_ID, "short", RUN),
                                     (REQUEST_ID, COMMIT, "-1")):
            with self.assertRaisesRegex(ValueError, "STATUS_LOCATOR_INPUT_INVALID"):
                status.status_payload(request_id, sha, run)


if __name__ == "__main__":
    unittest.main()
