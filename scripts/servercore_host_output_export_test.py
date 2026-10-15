"""Verify lossless Host TXT/ZIP export with UTF-8 and large streams."""
import hashlib
import json
import tempfile
import unittest
import zipfile
from pathlib import Path
from scripts.servercore_host_output_export import export_output


class ExportTests(unittest.TestCase):
    def test_zip_is_lossless_and_manifest_matches(self):
        rid = "req_" + "a" * 24
        out = "日本語Ω\n" * 300000
        err = "error\n" * 90000
        with tempfile.TemporaryDirectory() as d:
            Path(d, rid + ".json").write_text(json.dumps({
                "request_id": rid, "stdout": out, "stderr": err}), encoding="utf-8")
            target = Path(d, "output.zip")
            meta = export_output(rid, target, result_dir=d, zipped=True)
            with zipfile.ZipFile(target) as z:
                self.assertEqual(z.read("stdout.txt"), out.encode())
                self.assertEqual(z.read("stderr.txt"), err.encode())
                self.assertEqual(json.loads(z.read("manifest.json")), meta)
                self.assertEqual(meta["streams"]["stdout.txt"]["sha256"], hashlib.sha256(out.encode()).hexdigest())

    def test_text_export_is_not_truncated(self):
        rid = "req_" + "b" * 24
        out = "x" * 100000
        with tempfile.TemporaryDirectory() as d:
            Path(d, rid + ".json").write_text(json.dumps({"request_id": rid, "stdout": out}), encoding="utf-8")
            target = Path(d, "output.txt")
            export_output(rid, target, result_dir=d)
            self.assertEqual(target.read_text(), out)


if __name__ == "__main__":
    unittest.main()
