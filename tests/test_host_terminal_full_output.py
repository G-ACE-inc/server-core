"""Lossless host terminal output retrieval regression."""
import hashlib
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
from servercore_host_output_read import chunk
from servercore_service_deploy_socket import host_command_wire_reply


class HostOutputExport(unittest.TestCase):
    def test_full_txt_and_zip_export(self):
        from servercore_host_output_export import export_output
        import zipfile
        rid = "req_" + "c" * 24
        stdout = "日本語Ω" * 300000
        stderr = "ERR" * 100000
        with tempfile.TemporaryDirectory() as d:
            Path(d, rid + ".json").write_text(json.dumps({
                "request_id": rid, "stdout": stdout, "stderr": stderr}), encoding="utf-8")
            target = Path(d, "output.zip")
            metadata = export_output(rid, target, result_dir=d, zipped=True)
            with zipfile.ZipFile(target) as archive:
                self.assertEqual(archive.read("stdout.txt"), stdout.encode())
                self.assertEqual(archive.read("stderr.txt"), stderr.encode())
                self.assertEqual(json.loads(archive.read("manifest.json")), metadata)
            txt = Path(d, "output.txt")
            export_output(rid, txt, result_dir=d)
            self.assertEqual(txt.read_bytes(), stdout.encode())


class HostOutputChunks(unittest.TestCase):
    def test_multimegabyte_output_persisted_and_retrieved_without_loss(self):
        request_id = "req_" + "a" * 24
        stdout = "日本語Ω" * 650000
        stderr = "e" * 300000
        with tempfile.TemporaryDirectory() as dirname:
            Path(dirname, request_id + ".json").write_text(
                json.dumps({"request_id": request_id, "stdout": stdout, "stderr": stderr}),
                encoding="utf-8",
            )
            for stream, original in (("stdout", stdout), ("stderr", stderr)):
                parts = []
                offset = 0
                while True:
                    page = chunk(request_id, stream, offset, 8192, dirname)
                    parts.append(page["data"])
                    offset = page["next_offset"]
                    if page["complete"]:
                        break
                self.assertEqual("".join(parts), original)
                self.assertEqual(page["sha256"], hashlib.sha256(original.encode()).hexdigest())

    def test_wire_reply_retains_large_result_in_ledger(self):
        request_id = "req_" + "b" * 24
        stdout = "x" * (9 * 1024 * 1024)
        reply = {"ok": True, "request_id": request_id, "stdout": stdout, "stderr": ""}
        packed = host_command_wire_reply(reply)
        self.assertEqual(packed["stdout"], "")
        self.assertEqual(packed["stdout_chars"], len(stdout))
        self.assertTrue(packed["stdout_stored_complete"])
        self.assertEqual(packed["output_record_request_id"], request_id)
        self.assertEqual(packed["stdout_sha256"], hashlib.sha256(stdout.encode()).hexdigest())


class HostArtifactAssembler(unittest.TestCase):
    def test_large_reassembled_artifact_and_missing_page_denial(self):
        import zipfile
        from scripts.servercore_host_output_artifact_assemble import assemble
        rid = "req_" + "f" * 24
        stdout = "日本語Ω🙂" * 45000
        stderr = "err" * 10000

        def make_pages(stream, value):
            digest = hashlib.sha256(value.encode("utf-8")).hexdigest()
            for offset in range(0, max(1, len(value)), 8192):
                data = value[offset:offset + 8192]
                nxt = offset + len(data)
                yield {"request_id": rid, "stream": stream, "offset": offset,
                       "next_offset": nxt, "total_chars": len(value),
                       "complete": nxt == len(value), "sha256": digest, "data": data}

        chunks = [*make_pages("stdout", stdout), *make_pages("stderr", stderr)]
        with tempfile.TemporaryDirectory() as d:
            target = Path(d, "verified")
            meta = assemble(chunks, target)
            self.assertEqual((target / "stdout.txt").read_bytes(), stdout.encode())
            with zipfile.ZipFile(target / "output.zip") as z:
                self.assertEqual(z.read("stderr.txt"), stderr.encode())
                self.assertEqual(json.loads(z.read("manifest.json")), meta)
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaises(ValueError):
                assemble(chunks[1:], Path(d, "missing"))

if __name__ == "__main__":
    unittest.main()
