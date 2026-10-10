#!/usr/bin/env python3
"""Scoped, fail-closed evidence validator for GPT CHAT rule re-anchor receipts.

This validates *supplied evidence only*. It cannot intercept ChatGPT messages,
prove a model read an external source, or enforce a turn's duration.
"""
import json
import re
import sys

ORDER = ("開発目的", "作業目的", "作業内容", "NEXT", "プロジェクト進行表")
FIELDS = (
    "project_purpose_canonical", "master_latest_intent", "current_work_purpose",
    "current_task", "last_confirmed_state", "next_action",
    "must_preserve", "must_not_happen", "blocker", "rule_revision",
    "owner_cu", "current_issue_url", "readback_verified",
)
URL = re.compile(r"^https://github\.com/[^/]+/[^/]+/issues/[1-9][0-9]*$")
HEAD = re.compile(r"(?m)^#{1,3}\s*(開発目的|作業目的|作業内容|NEXT|プロジェクト進行表)\s*$")
ACTION_REF = re.compile(r"^https://github\.com/[^/]+/[^/]+/(?:actions/runs/[1-9][0-9]*|commit/[0-9a-f]{40})$")


def validate(receipt, expected=None):
    errors = []
    if not isinstance(expected, dict):
        return ["TRUSTED_EXPECTATIONS_MISSING"]
    for field in ("owner_cu", "rule_revision", "project_purpose_canonical", "current_issue_url"):
        if not isinstance(expected.get(field), str) or not expected[field].strip():
            errors.append("EXPECTED_" + field.upper() + "_MISSING")
    if not isinstance(receipt, dict):
        return ["RECEIPT_NOT_OBJECT"]
    for key in FIELDS:
        val = receipt.get(key)
        if (not isinstance(val, str) or not val.strip()) and key != "readback_verified":
            errors.append("MISSING_" + key.upper())
    if receipt.get("readback_verified") is not True:
        errors.append("CURRENT_NOT_READ_BACK")
    if not isinstance(receipt.get("current_issue_url"), str) or not URL.fullmatch(receipt["current_issue_url"]):
        errors.append("CURRENT_ISSUE_INVALID")
    if receipt.get("owner_cu") != expected.get("owner_cu"):
        errors.append("CU_OWNER_MISMATCH")
    if receipt.get("rule_revision") != expected.get("rule_revision"):
        errors.append("RULE_STALE_OR_MISMATCH")
    if receipt.get("project_purpose_canonical") != expected.get("project_purpose_canonical"):
        errors.append("CANONICAL_PURPOSE_MISMATCH")
    if receipt.get("current_issue_url") != expected.get("current_issue_url"):
        errors.append("CURRENT_SOURCE_MISMATCH")
    if receipt.get("next_action") == "NONE" and receipt.get("outstanding_in_scope_work") is True:
        errors.append("UNFINISHED_WORK_NOT_RESOLVED")
    # These refs must originate from an independently checked trusted Current,
    # not a report self-assertion. This is structural, not an API/runtime hook.
    if receipt.get("outstanding_in_scope_work") is True:
        status = receipt.get("turn_continuation")
        if status == "MASTER_PAUSED" and expected.get("master_pause_authorized") is True:
            pass
        elif status != "EXECUTED_TO_SAFE_GATE":
            errors.append("TURN_PREMATURELY_STOPPED")
        else:
            refs = receipt.get("executed_action_refs")
            verified = expected.get("verified_action_refs")
            if not isinstance(refs, list) or not refs:
                errors.append("EXECUTED_ACTION_EVIDENCE_MISSING")
            elif not isinstance(verified, list) or not verified or any(
                not isinstance(ref, str) or not ACTION_REF.fullmatch(ref)
                or ref not in verified for ref in refs
            ):
                errors.append("EXECUTED_ACTION_EVIDENCE_NOT_TRUSTED")
            if receipt.get("failed_step"):
                after_refs = receipt.get("post_failure_action_refs")
                if not isinstance(after_refs, list) or not after_refs:
                    errors.append("POST_FAILURE_ACTION_MISSING")
                elif (not isinstance(refs, list) or
                      any(ref not in refs for ref in after_refs) or
                      receipt.get("failed_step_evidence_ref") in after_refs):
                    errors.append("POST_FAILURE_ACTION_NOT_DISTINCT")
    report = receipt.get("report")
    if not isinstance(report, str):
        errors.append("REPORT_MISSING")
    else:
        headings = HEAD.findall(report)
        if tuple(headings) != ORDER:
            errors.append("REPORT_ORDER_INVALID")
        else:
            purpose = report.splitlines()
            first = next((i for i, ln in enumerate(purpose) if HEAD.fullmatch(ln)), -1)
            second = next((i for i in range(first + 1, len(purpose)) if HEAD.fullmatch(purpose[i])), len(purpose))
            actual = "\n".join(purpose[first + 1:second]).strip()
            if actual != receipt.get("project_purpose_canonical"):
                errors.append("PROJECT_PURPOSE_CHANGED")
        if "➔今ここ" not in report:
            errors.append("CURRENT_POSITION_MISSING")
    return errors


def main():
    if len(sys.argv) != 3:
        print("usage: gpt_chat_receipt_gate.py receipt.json trusted-current.json", file=sys.stderr)
        return 2
    with open(sys.argv[1], encoding="utf-8") as fh:
        receipt = json.load(fh)
    with open(sys.argv[2], encoding="utf-8") as fh:
        expected = json.load(fh)
    errors = validate(receipt, expected)
    print(json.dumps({"status": "FAIL" if errors else "PASS", "errors": errors}, ensure_ascii=False))
    return 1 if errors else 0


if __name__ == "__main__":
    raise SystemExit(main())
