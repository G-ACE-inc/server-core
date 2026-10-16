"""CU40 full Writer -> ZIP -> encrypted Gateway inbox -> Vault -> private GH handoff."""
import base64
import hashlib
import json
import tempfile
import unittest
from pathlib import Path
from scripts.servercore_host_output_export import export_output
from scripts.servercore_host_output_cipher_inbox import store
from scripts.servercore_host_output_private_artifact_publish import run

RID="req_"+"9"*24

class Reply:
    status=200
    def __init__(self,obj):self.data=json.dumps(obj).encode()
    def __enter__(self):return self
    def __exit__(self,*args):return False
    def read(self,n):return self.data[:n]

class MockVault:
    def __init__(self,fragments):self.fragments=fragments;self.fail=False
    def __call__(self,request):
        req=json.loads(request.data)
        assert request.full_url.endswith("/internal/v1/crypto/unseal")
        i=int.from_bytes(base64.b64decode(req["iv"]),"big")
        raw=self.fragments[i]
        if self.fail:raw=b"altered"
        return Reply({"plaintext_base64":base64.b64encode(raw).decode()})

class MockRelease:
    def __init__(self):self.calls=[]
    def __call__(self,args,**_):
        self.calls.append(args)
        class Result:returncode=0
        return Result()

def setup(directory):
    root=Path(directory)
    stdout="日本語Ω🙂\n"*30000
    stderr="error日本語\n"*12000
    (root/(RID+".json")).write_text(json.dumps({"request_id":RID,"stdout":stdout,"stderr":stderr}),encoding="utf-8")
    zip_path=root/"source.zip"
    export_output(RID,zip_path,result_dir=root,zipped=True)
    data=zip_path.read_bytes()
    fragments=[data[i:i+131072] for i in range(0,len(data),131072)]
    inbox=root/"cipher"
    for i,part in enumerate(fragments):
        ct=base64.b64encode(b"x"*(len(part)+16)).decode()
        iv=base64.b64encode(i.to_bytes(12,"big")).decode()
        store({"schema":"gace.host-output.encrypted-chunk/v1",
          "request_id":RID,"zip_sha256":hashlib.sha256(data).hexdigest(),
          "zip_bytes":len(data),"total_parts":len(fragments),"index":i,
          "chunk_bytes":len(part),"chunk_sha256":hashlib.sha256(part).hexdigest(),
          "vault_ref":"registered-ref","consumer":"g-ace-workspace",
          "iv":iv,"ciphertext_parts":[ct[j:j+3000] for j in range(0,len(ct),3000)]},
          root=inbox)
    return inbox,fragments,stdout,stderr

class FullBridgeTests(unittest.TestCase):
    def test_full_verified_zip_and_private_release_only_after_original_hash(self):
        with tempfile.TemporaryDirectory() as d:
            inbox,frags,out,err=setup(d)
            mock=MockVault(frags)
            gh=MockRelease()
            v=run(RID,cipher_root=inbox,writer_dir=d,vault_base="http://127.0.0.1:8791",
                  vault_token="x",opener=mock,runner=gh)
            self.assertEqual(v["state"],"PRIVATE_RELEASE_PUBLISHED_AWAIT_ARTIFACT")
            self.assertEqual(v["streams"]["stdout"]["bytes"],len(out.encode()))
            self.assertEqual(v["streams"]["stderr"]["chars"],len(err))
            self.assertEqual(len(gh.calls),2)
            self.assertEqual(gh.calls[0][:3],["gh","release","create"])
            self.assertIn("seigo-gace/TGserver",gh.calls[0])

    def test_corrupt_unseal_denied_without_github_upload(self):
        with tempfile.TemporaryDirectory() as d:
            inbox,frags,*_=setup(d)
            mock=MockVault(frags);mock.fail=True
            gh=MockRelease()
            with self.assertRaisesRegex(ValueError,"UNSEALED_CHUNK_DIGEST_MISMATCH"):
                run(RID,cipher_root=inbox,writer_dir=d,vault_base="http://127.0.0.1:8791",
                    vault_token="x",opener=mock,runner=gh)
            self.assertEqual(gh.calls,[])

if __name__=="__main__": unittest.main()
