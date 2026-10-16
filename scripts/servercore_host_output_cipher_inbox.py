"""Receive Gateway-authenticated encrypted Host ZIP chunks over existing result socket.

Only ciphertext is persisted; original stdout/stderr never touch public Issues.
Socket peer admission remains owned by existing result sink / receiver.
"""
import base64
import hashlib
import json
import os
import re
import tempfile
from pathlib import Path

SCHEMA = "gace.host-output.encrypted-chunk/v1"
RID = re.compile(r"req_[0-9a-f]{24}\Z")
SHA = re.compile(r"[a-f0-9]{64}\Z")
IDENT = re.compile(r"[A-Za-z0-9._:/-]{1,160}\Z")
MAX_CHUNKS = 8192
MAX_CIPHER_CHARS = 200000
DEFAULT_DIR = Path("/run/gace/host-output-inbox")


class InboxError(ValueError):
    pass


def valid(data):
    if not isinstance(data, dict) or set(data) != {
        "schema", "request_id", "zip_sha256", "zip_bytes", "total_parts",
        "index", "chunk_bytes", "chunk_sha256", "vault_ref", "consumer",
        "ciphertext_parts", "iv"
    } or data["schema"] != SCHEMA:
        raise InboxError("ENVELOPE_INVALID")
    if not isinstance(data["request_id"], str) or not RID.fullmatch(data["request_id"]):
        raise InboxError("REQUEST_ID_INVALID")
    if not isinstance(data["zip_sha256"], str) or not SHA.fullmatch(data["zip_sha256"]):
        raise InboxError("ZIP_SHA_INVALID")
    if not isinstance(data["chunk_sha256"], str) or not SHA.fullmatch(data["chunk_sha256"]):
        raise InboxError("CHUNK_SHA_INVALID")
    total, n, i, size = (data[k] for k in ("zip_bytes", "total_parts", "index", "chunk_bytes"))
    if any(type(x) is not int for x in (total,n,i,size)) or not 0 < total <= (1024*1024*1024) or not 1 <= n <= MAX_CHUNKS or not 0 <= i < n or not 0 < size <= 131072:
        raise InboxError("CHUNK_BOUNDS_INVALID")
    if (total + 131071)//131072 != n:
        raise InboxError("PART_COUNT_MISMATCH")
    if size != min(131072,total-i*131072):
        raise InboxError("CHUNK_LENGTH_MISMATCH")
    for field in ("vault_ref","consumer"):
        if not isinstance(data[field],str) or not IDENT.fullmatch(data[field]):
            raise InboxError("VAULT_ID_INVALID")
    pieces=data["ciphertext_parts"]
    if not isinstance(pieces,list) or not pieces or any(not isinstance(x,str) or not 1 <= len(x) <= 3000 for x in pieces) or sum(map(len,pieces)) > MAX_CIPHER_CHARS:
        raise InboxError("CIPHER_PARTS_INVALID")
    try:
        c64="".join(pieces)
        ciphertext=base64.b64decode(c64,validate=True)
        iv=base64.b64decode(data["iv"],validate=True)
        if base64.b64encode(ciphertext).decode()!=c64 or len(ciphertext)!=size+16 or len(iv)!=12 or base64.b64encode(iv).decode()!=data["iv"]:
            raise ValueError()
    except (ValueError,TypeError):
        raise InboxError("CIPHER_AUTH_SHAPE_INVALID") from None
    return data


def store(envelope, *, root=DEFAULT_DIR):
    e=valid(envelope)
    root=Path(root)
    if root.is_symlink():
        raise InboxError("INBOX_SYMLINK_DENIED")
    root.mkdir(mode=0o700,parents=True,exist_ok=True)
    target_dir=root/e["request_id"]
    if target_dir.is_symlink():
        raise InboxError("INBOX_SYMLINK_DENIED")
    target_dir.mkdir(mode=0o700,exist_ok=True)
    # Only this request_id and part index are used as file paths.
    path=target_dir/(f"{e['index']:05d}.json")
    encoded=json.dumps(e,sort_keys=True,separators=(",",":")).encode("utf-8")
    if path.exists():
        if path.is_symlink():
            raise InboxError("INBOX_SYMLINK_DENIED")
        if path.read_bytes()!=encoded:
            raise InboxError("CHUNK_REPLAY_CONFLICT")
        return {"state":"DUPLICATE","request_id":e["request_id"],"index":e["index"]}
    with tempfile.NamedTemporaryFile(dir=target_dir,prefix=".pending-",delete=False) as output:
        pending=Path(output.name)
        os.chmod(output.name,0o600)
        output.write(encoded)
        output.flush()
        os.fsync(output.fileno())
    try:
        # Exclusive creation avoids overwriting another raced receipt.
        try:
            os.link(pending,path)
        except FileExistsError:
            if path.is_symlink() or path.read_bytes()!=encoded:
                raise InboxError("CHUNK_REPLAY_CONFLICT")
        return {"state":"STORED","request_id":e["request_id"],"index":e["index"]}
    finally:
        pending.unlink(missing_ok=True)


def collect(request_id, *, root=DEFAULT_DIR):
    if not isinstance(request_id,str) or not RID.fullmatch(request_id):
        raise InboxError("REQUEST_ID_INVALID")
    directory=Path(root)/request_id
    if directory.is_symlink() or not directory.is_dir():
        raise InboxError("INBOX_NOT_FOUND")
    parts=[]
    for path in sorted(directory.glob("*.json")):
        if path.is_symlink():
            raise InboxError("INBOX_SYMLINK_DENIED")
        parts.append(valid(json.loads(path.read_text())))
    if not parts:
        raise InboxError("INBOX_EMPTY")
    first=parts[0]
    if len(parts)!=first["total_parts"] or [p["index"] for p in parts]!=list(range(first["total_parts"])):
        raise InboxError("INBOX_INCOMPLETE")
    for p in parts:
        if any(p[k]!=first[k] for k in ("request_id","zip_sha256","zip_bytes","total_parts","vault_ref","consumer")):
            raise InboxError("INBOX_CORRELATION_MISMATCH")
    return parts
