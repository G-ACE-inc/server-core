"""Regression checks for lossless, fail-closed Host page reconstruction."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.servercore_host_output_artifact_assemble import assemble


RID = "req_" + "d" * 24


def pages(stream, value, size=8192):
    sha = hashlib.sha256(value.encode("utf-8")).hexdigest()
    for offset in range(0, max(len(value), 1), size):
        data = value[offset:offset + size]
        nxt = offset + len(data)
        yield {"request_id": RID, "stream": stream, "offset": offset,
               "next_offset": nxt, "total_chars": len(value),
               "complete": nxt == len(value), "sha256": sha, "data": data}


class AssembleTests(unittest.TestCase):
    def test_large_unicode_lossless_zip_and_text(self):
        stdout = "日本語Ω🙂\\n" * 90000
        stderr = "error\n" * 50000
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory, "artifact")
            manifest = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], output)
            self.assertEqual((output / "stdout.txt").read_bytes(), stdout.encode())
            self.assertEqual((output / "stderr.txt").read_bytes(), stderr.encode())
            with zipfile.ZipFile(output / "output.zip") as z:
                self.assertEqual(z.read("stdout.txt"), stdout.encode())
                self.assertEqual(z.read("stderr.txt"), stderr.encode())
                self.assertEqual(json.loads(z.read("manifest.json")), manifest)

    def test_empty_streams(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory, "artifact")
            assemble([*pages("stdout", ""), *pages("stderr", "")], output)
            self.assertEqual((output / "stdout.txt").read_bytes(), b"")

    def test_missing_or_overlapping_page_fails_without_creating_output(self):
        base = [*pages("stdout", "x" * 18000), *pages("stderr", "")]
        scenarios = [
            base[1:],
            base + [base[-1]],
            [*base[:-1], {**base[-1], "request_id": "req_" + "e" * 24}],
            [*base[:-1], {**base[-1], "data": "tampered"}],
        ]
        for case in scenarios:
            with self.subTest(case=len(case)), tempfile.TemporaryDirectory() as directory:
                output = Path(directory, "artifact")
                with self.assertRaises(ValueError):
                    assemble(case, output)
                self.assertFalse(output.exists())


if __name__ == "__main__":
    unittest.main()
