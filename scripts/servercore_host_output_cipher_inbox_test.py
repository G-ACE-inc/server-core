"""CU40: ciphertext-only sink uses existing Host UNIX socket and private inbox."""
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.servercore_host_output_cipher_inbox import InboxError, store, collect

RID="req_"+"a"*24

def envelope(index, total_parts=2, total_bytes=131079):
    chunk_size=min(131072,total_bytes-index*131072)
    cipher=b"x"*(chunk_size+16)
    encoded=base64.b64encode(cipher).decode()
    return {
        "schema":"gace.host-output.encrypted-chunk/v1",
        "request_id":RID,
        "zip_sha256":"b"*64,
        "zip_bytes":total_bytes,
        "total_parts":total_parts,
        "index":index,
        "chunk_bytes":chunk_size,
        "chunk_sha256":hashlib.sha256(b"n"*chunk_size).hexdigest(),
        "vault_ref":"preauthorized-vault-key-id",
        "consumer":"g-ace-workspace",
        "iv":base64.b64encode(b"i"*12).decode(),
        "ciphertext_parts":[encoded[i:i+3000] for i in range(0,len(encoded),3000)]
    }

class CipherInboxTests(unittest.TestCase):
    def test_lossless_valid_chunk_retry_and_complete_collection(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=envelope(0)
            b=envelope(1)
            self.assertEqual(store(a,root=tmp)["state"],"STORED")
            self.assertEqual(store(a,root=tmp)["state"],"DUPLICATE")
            self.assertEqual(store(b,root=tmp)["state"],"STORED")
            restored=collect(RID,root=tmp)
            self.assertEqual(restored,[a,b])
            self.assertFalse(any("plaintext" in str(x) for x in restored))
            self.assertEqual(len(list(Path(tmp,RID).glob("*.json"))),2)
            # Only cipher files, never stdout/stderr text.
            self.assertNotIn("PRIVATE_STDOUT",Path(tmp,RID,"00000.json").read_text())

    def test_reject_missing_tampered_conflicting_parts(self):
        with tempfile.TemporaryDirectory() as tmp:
            a=envelope(0)
            store(a,root=tmp)
            with self.assertRaisesRegex(InboxError,"INBOX_INCOMPLETE"):
                collect(RID,root=tmp)
            changed={**a,"zip_sha256":"c"*64}
            with self.assertRaisesRegex(InboxError,"CHUNK_REPLAY_CONFLICT"):
                store(changed,root=tmp)
            bad={**a,"ciphertext_parts":["key=secret-value"]}
            with self.assertRaisesRegex(InboxError,"CIPHER_AUTH_SHAPE_INVALID"):
                store(bad,root=tmp)
            with self.assertRaisesRegex(InboxError,"CHUNK_BOUNDS_INVALID"):
                store({**a,"chunk_bytes":-1},root=tmp)

if __name__=="__main__": unittest.main()
