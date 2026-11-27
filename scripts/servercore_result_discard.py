#!/usr/bin/env python3
"""Inspect or retire exact unpublished FAIL receipts; never dispatch Host work."""

import argparse
import json
from pathlib import Path

from servercore_result_sink import SinkError, discard_failed_record, read_record


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--result-dir", type=Path, required=True)
    parser.add_argument("--request-id", action="append", required=True)
    parser.add_argument("--apply", action="store_true")
    args = parser.parse_args(argv)
    if len(args.request_id) != len(set(args.request_id)):
        parser.error("duplicate request ID")
    rows = []
    for request_id in args.request_id:
        try:
            record = read_record(request_id, args.result_dir)
        except SinkError as exc:
            parser.error(str(exc))
        if not record or record.get("request_id") != request_id:
            parser.error("DISCARD_RECORD_NOT_FOUND")
        if record.get("state") != "FAIL" or record.get("published"):
            parser.error("DISCARD_NOT_UNPUBLISHED_FAILURE")
        rows.append({"request_id": request_id, "state": record["state"],
                     "already_discarded": bool(record.get("discarded"))})
    if args.apply:
        for row in rows:
            row["disposition"] = discard_failed_record(
                row["request_id"], result_dir=args.result_dir)
    print(json.dumps({"mode": "APPLY" if args.apply else "DRY_RUN", "records": rows}, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
