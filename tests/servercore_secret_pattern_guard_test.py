import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
import servercore_secret_pattern_guard as guard  # noqa: E402


def line(content):
    return "sample.txt:1:" + content


class SecretPatternGuardTests(unittest.TestCase):
    def test_code_reads_are_ignored(self):
        samples = [
            "token=fs.readFileSync(process.env.BOT_TOKEN_FILE)",
            "token=process.env.BOT_TOKEN_FILE?fs.readFileSync(x)",
            "token=oauth.refresh_if_needed()",
            "token=source_token(path)",
            "gateway_token=os.environ.get(\"NAME\", \"\")",
            "secret=os.environ.get(\"NAME\")",
        ]
        for sample in samples:
            self.assertEqual(guard.classify_grep_line(line(sample)), "code", sample)

    def test_literals_still_fail(self):
        samples = [
            "password=correcthorsebatterystaple",
            'token = "ghp_1234567890abcdef"',
            "api_key=sk-live-1234567890abcd",
            "token=eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.signaturevalue",
            "password=correct.horse.battery",
        ]
        for sample in samples:
            self.assertEqual(guard.classify_grep_line(line(sample)), "literal", sample)

    def test_unparsed_input_fails_closed(self):
        self.assertEqual(guard.real_hit_locations(["not a grep line"]), ["unparsed"])

    def test_locations_omit_matched_text(self):
        locations = guard.real_hit_locations([
            line("token=fs.readFileSync(file)"),
            "dir/config.json:4:password=correcthorsebatterystaple",
        ])
        self.assertEqual(locations, ["dir/config.json:4:literal"])

    def test_current_tree_has_no_literal_hits(self):
        scan = subprocess.run(
            [
                "git", "grep", "-nEI",
                "(api[_-]?key|secret|token|password|credential|session)"
                "[[:alnum:]_ -]*[:=][[:space:]]*[\"]?[A-Za-z0-9_./+=-]{12,}",
                "--",
                ":!docs/**",
                ":!archive/**",
                ":!.github/workflows/server-core-guard.yml",
                ":!scripts/ai-auto-commit.sh",
                ":!.github/chat-host-requests/req_e8a16f43db952c78041ad6b9.json",
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            check=False,
        )
        self.assertIn(scan.returncode, (0, 1))
        self.assertEqual(guard.real_hit_locations(scan.stdout.splitlines()), [])


if __name__ == "__main__":
    unittest.main()
