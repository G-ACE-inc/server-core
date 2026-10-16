"""Regression checks for lossless, fail-closed Host page reconstruction."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.servercore_host_output_artifact_assemble import (
    MAX_VERIFIED_STREAM_BYTES, assemble, verify_artifact_zip)


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

    def test_chat_readback_verifies_large_unicode_bytes_hash_and_chars(self):
        stdout = "日本語Ω🙂\n" * 120000
        stderr = "error 日本語\n" * 17000
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "artifact")
            meta = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], target)
            expected = {
                "stdout": {"sha256": meta["streams"]["stdout.txt"]["sha256"], "chars": len(stdout), "bytes": len(stdout.encode("utf-8"))},
                "stderr": {"sha256": meta["streams"]["stderr.txt"]["sha256"], "chars": len(stderr), "bytes": len(stderr.encode("utf-8"))},
            }
            result = verify_artifact_zip(target / "output.zip", RID, expected)
            self.assertTrue(result["output_complete"])
            self.assertEqual(result["streams"]["stdout"]["bytes"], len(stdout.encode("utf-8")))
            self.assertEqual(result["streams"]["stderr"]["chars"], len(stderr))
            self.assertNotIn("日本語", json.dumps(result, ensure_ascii=False))
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_REQUEST_MISMATCH"):
                verify_artifact_zip(target / "output.zip", "req_" + "e" * 24, expected)
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_DIGEST_OR_LENGTH_MISMATCH"):
                verify_artifact_zip(target / "output.zip", RID,
                                    {**expected, "stdout": {**expected["stdout"], "chars": len(stdout) + 1}})
            with self.assertRaisesRegex(ValueError, "EXPECTED_HOST_STREAM_METADATA_REQUIRED"):
                verify_artifact_zip(target / "output.zip", RID, None)
            # A matching ZIP-internal manifest cannot substitute the trusted
            # Writer's independent expected byte count.
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_MANIFEST_MISMATCH"):
                verify_artifact_zip(target / "output.zip", RID,
                    {**expected, "stdout": {**expected["stdout"], "bytes": expected["stdout"]["bytes"] + 1}})
            with self.assertRaisesRegex(ValueError, "EXPECTED_HOST_STREAM_METADATA_INVALID"):
                verify_artifact_zip(target / "output.zip", RID,
                    {**expected, "stdout": {**expected["stdout"], "bytes": None}})

    def test_authenticated_expected_size_limit_rejected_before_extracting(self):
        stdout, stderr = "safe", ""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "artifact")
            meta = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], target)
            expected = {
                name: {"sha256": meta["streams"][name + ".txt"]["sha256"],
                       "chars": len(data), "bytes": len(data.encode("utf-8"))}
                for name, data in (("stdout", stdout), ("stderr", stderr))
            }
            oversize = {**expected, "stdout": {**expected["stdout"],
                         "bytes": MAX_VERIFIED_STREAM_BYTES + 1}}
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_UNCOMPRESSED_SIZE_LIMIT"):
                verify_artifact_zip(target / "output.zip", RID, oversize)

    def test_high_ratio_archive_denied_but_ordinary_unicode_allowed(self):
        stdout, stderr = "A" * 2_000_000, ""
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "artifact")
            meta = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], target)
            expected = {
                name: {"sha256": meta["streams"][name + ".txt"]["sha256"],
                       "chars": len(data), "bytes": len(data.encode("utf-8"))}
                for name, data in (("stdout", stdout), ("stderr", stderr))
            }
            with self.assertRaisesRegex(ValueError, "HOST_OUTPUT_EXPANSION_LIMIT"):
                verify_artifact_zip(target / "output.zip", RID, expected)

    def test_host_archive_tamper_duplicate_and_missing_denied(self):
        stdout, stderr = "x日本語" * 20, "error"
        with tempfile.TemporaryDirectory() as directory:
            target = Path(directory, "artifact")
            meta = assemble([*pages("stdout", stdout), *pages("stderr", stderr)], target)
            expected = {name: {"sha256": meta["streams"][name + ".txt"]["sha256"],
                                "chars": len(value), "bytes": len(value.encode("utf-8"))}
                        for name, value in (("stdout", stdout), ("stderr", stderr))}
            original = json.loads((target / "manifest.json").read_text())
            cases = [
                [("stdout.txt", "tampered"), ("stderr.txt", stderr),
                 ("manifest.json", json.dumps(original))],
                [("stdout.txt", stdout), ("stderr.txt", stderr),
                 ("manifest.json", json.dumps(original)), ("extra", "no")],
                [("stdout.txt", stdout), ("manifest.json", json.dumps(original))],
            ]
            for index, entries in enumerate(cases):
                path = Path(directory, f"bad{index}.zip")
                with zipfile.ZipFile(path, "w") as archive:
                    for name, value in entries:
                        archive.writestr(name, value)
                with self.subTest(index=index), self.assertRaises(ValueError):
                    verify_artifact_zip(path, RID, expected)

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
