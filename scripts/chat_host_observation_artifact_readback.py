#!/usr/bin/env python3
"""Validate an existing common CHAT Host observation artifact for safe CU recovery.

The GitHub connector or gh API fetches the ZIP by verified run/artifact ID.
This module does not dispatch Host commands or read Issue comment history.
"""
import argparse
import json
import re
import zipfile
from pathlib import Path

REQ = re.compile(r"req_[0-9a-f]{24}\Z")
SHA = re.compile(r"[a-f0-9]{40}\Z")
DIGEST = re.compile(r"[a-f0-9]{64}\Z")
OBSERVATIONS = {
    "HOST_RESULT_NOT_RETURNED", "HOST_OUTPUT_PARTIAL", "HOST_OPERATION_PASSED",
    "HOST_SOURCE_SHA_MISMATCH", "HOST_OPERATION_FAILED", "HOST_RESULT_UNVERIFIED",
    "CORRELATION_FAILED",
}
STREAM_KEYS = {"stdout", "stderr"}


def validate(receipt, expected_request_id):
    if not isinstance(receipt, dict) or not REQ.fullmatch(expected_request_id):
        raise ValueError("INVALID_REQUEST")
    if receipt.get("request_id") != expected_request_id:
        raise ValueError("REQUEST_MISMATCH")
    obs, action = receipt.get("observation"), receipt.get("next_action")
    if obs not in OBSERVATIONS or not isinstance(action, str) or not action or len(action) > 120:
        raise ValueError("OBSERVATION_INVALID")
    verified = receipt.get("result_verified")
    if type(verified) is not bool:
        raise ValueError("VERIFICATION_INVALID")
    if obs == "HOST_RESULT_NOT_RETURNED":
        if verified is not False:
            raise ValueError("MISSING_RESULT_VERIFIED")
    else:
        if receipt.get("command_id") not in ("host.command", "dev.job", "invalid.request"):
            raise ValueError("COMMAND_INVALID")
        if not isinstance(receipt.get("expected_sha"), str) or not SHA.fullmatch(receipt["expected_sha"]):
            raise ValueError("EXPECTED_SHA_INVALID")
        stream_data = receipt.get("streams")
        if not isinstance(stream_data, dict) or set(stream_data) != STREAM_KEYS:
            raise ValueError("STREAMS_MISSING")
        for info in stream_data.values():
            if not isinstance(info, dict) or type(info.get("complete")) is not bool:
                raise ValueError("STREAM_STATE_INVALID")
            digest = info.get("sha256")
            if digest is not None and (not isinstance(digest, str) or not DIGEST.fullmatch(digest)):
                raise ValueError("STREAM_DIGEST_INVALID")
        if obs == "HOST_OUTPUT_PARTIAL" and all(info["complete"] for info in stream_data.values()):
            raise ValueError("PARTIAL_FLAG_MISMATCH")
    # Issue #10 metadata-only results contain Host ledger locators rather than
    # stdout/stderr bytes. The poller's 'complete' flag alone MUST NOT prove that
    # the CHAT received full output. Require verified digest + byte/char evidence.
    streams = receipt.get("streams") or {}
    stream_metadata_complete = (
        verified is True
        and set(streams) == STREAM_KEYS
        and all(
            info.get("complete") is True
            and isinstance(info.get("sha256"), str)
            and DIGEST.fullmatch(info["sha256"])
            and type(info.get("chars")) is int
            and info["chars"] >= 0
            for info in streams.values()
        )
    )
    if obs == "HOST_OPERATION_PASSED":
        action = "INSPECT_HOST_LEDGER_OUTPUT_COMPLETENESS_AND_CONTINUE"
    # Do not return unchecked free-form data, plaintext Host output, or credentials.
    return {
        "request_id": expected_request_id,
        "result_verified": verified,
        "observation": obs,
        "next_action": action,
        "result_url": receipt.get("result_url") if isinstance(receipt.get("result_url"), str) else None,
        "output_complete": False,  # This artifact contains metadata, never the Host payload.
        "stream_metadata_complete": stream_metadata_complete,
    }


def from_artifact(path, request_id):
    path = Path(path)
    with zipfile.ZipFile(path) as archive:
        names = archive.namelist()
        if names != ["gace-chat-host-observation.json"]:
            raise ValueError("ARTIFACT_CONTENT_INVALID")
        item = archive.getinfo(names[0])
        if item.file_size > 32768:
            raise ValueError("ARTIFACT_TOO_LARGE")
        receipt = json.loads(archive.read(item).decode("utf-8"))
    return validate(receipt, request_id)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("artifact_zip", help="GitHub Actions artifact downloaded from verified run")
    parser.add_argument("--request-id", required=True)
    args = parser.parse_args()
    print(json.dumps(from_artifact(args.artifact_zip, args.request_id), ensure_ascii=False))


if __name__ == "__main__":
    main()
