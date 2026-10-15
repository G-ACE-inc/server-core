import json
import tempfile
import unittest
from pathlib import Path
from scripts.chat_cu_continuation import persist_receipt

class ReceiptTests(unittest.TestCase):
    def test_roundtrip(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.json"
            payload={"checkpoint":{"request_id":"req_"+"a"*24},"continuation":{"next_action":"POLL_EXISTING_RUN"}}
            persist_receipt(p,payload)
            self.assertEqual(json.loads(p.read_text()),payload)
    def test_missing_continuation_denied(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"RECEIPT_INVALID"):
                persist_receipt(Path(d)/"receipt.json",{})
    def test_large_content_denied(self):
        with tempfile.TemporaryDirectory() as d:
            with self.assertRaisesRegex(ValueError,"RECEIPT_TOO_LARGE"):
                persist_receipt(Path(d)/"receipt.json",{"continuation":{"output":"A"*40000}})
    def test_symlink_denied(self):
        with tempfile.TemporaryDirectory() as d:
            p=Path(d)/"receipt.json"
            p.symlink_to(Path(d)/"target")
            with self.assertRaisesRegex(ValueError,"RECEIPT_SYMLINK_DENIED"):
                persist_receipt(p,{"continuation":{}})

if __name__=="__main__":
    unittest.main()
