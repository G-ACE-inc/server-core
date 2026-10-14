#!/usr/bin/env python3
"""Use a new, commit-unique CHAT request as a workspace-only Actions target."""
import json
import re
import subprocess
import sys
from pathlib import Path

PREFIX = ".github/chat-host-requests/"
REQUEST = re.compile(r"^[.]github/chat-host-requests/req_[a-f0-9]{24}[.]json$")
TARGET = Path("/tmp/gace-common-host-request.json")
LEGACY_TARGET = ".github/chatgpt-live-api-target.json"

def select(added, changed):
    candidates = [p for p in changed if p.startswith(PREFIX)]
    if not candidates:
        return None
    if len(candidates) != 1 or not REQUEST.fullmatch(candidates[0]):
        raise ValueError("REQUEST_PATH_DENIED")
    if candidates[0] not in added or LEGACY_TARGET in changed:
        raise ValueError("REQUEST_MUST_BE_NEW_AND_SEPARATE")
    return Path(candidates[0])

def git_paths(filter_added=False):
    cmd = ["git", "diff-tree", "--root", "--no-commit-id", "--name-only", "-r"]
    if filter_added:
        cmd += ["--diff-filter=A"]
    cmd += ["HEAD"]
    result = subprocess.run(cmd, text=True, capture_output=True, timeout=15)
    if result.returncode:
        raise ValueError("GIT_DIFF_FAILED")
    return result.stdout.splitlines()

def prepare(path):
    if path.is_symlink() or not path.is_file() or path.stat().st_size > 8192:
        raise ValueError("REQUEST_FILE_INVALID")
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or data.get("bounded_host_request", {}).get("enabled") is not True:
        raise ValueError("REQUEST_NOT_ENABLED")
    if data.get("chat_decision_checkpoint", {}).get("phase") != "START":
        raise ValueError("START_RECEIPT_MISSING")
    if data.get("gitops_request", {}).get("enabled") is not False or data.get("source_reflect_request", {}).get("enabled") is not False:
        raise ValueError("CONCURRENT_EFFECT_DENIED")
    if data.get("server_command_id") or data.get("run_id"):
        raise ValueError("OTHER_COMMAND_DENIED")
    return data

def main():
    try:
        selected = select(git_paths(True), git_paths())
        if selected is None:
            print("CHAT_ISOLATED_REQUEST=NONE")
            return 0
        data = prepare(selected)
        TARGET.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        print("CHAT_ISOLATED_REQUEST=SELECTED")
        print("CHAT_ISOLATED_REQUEST_FILE=" + str(selected))
        return 0
    except (ValueError, TypeError, AttributeError, OSError, subprocess.TimeoutExpired) as exc:
        print("CHAT_ISOLATED_REQUEST=DENIED")
        print("CHAT_ISOLATED_REQUEST_ERROR=" + str(exc)[:100])
        return 1

if __name__ == "__main__":
    sys.exit(main())
