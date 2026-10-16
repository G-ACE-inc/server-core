#!/usr/bin/env python3
"""Nonexecuting command checks and lossless assembly for the existing Host lane.

No dispatch, authority receipt generation, network call or command execution.
"""
import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import secrets
import shlex
import subprocess
import sys

# Deliberately recognize standalone heredoc openers, not arbitrary shell code.
# Bodies of other recognized heredocs are skipped, including shell-looking text.
HEREDOC = re.compile(
    r'''^\s*(?P<argv>.+?)\s*<<(?P<tabs>-?)\s*(?:(?P<quote>['"])(?P<quoted>[A-Za-z_]\w*)(?P=quote)|(?P<plain>[A-Za-z_]\w*))\s*$''')
PYTHON = re.compile(r"(?:/usr/bin/)?python(?:3(?:\.\d+)?)?\Z")


def check_python(source):
    try:
        compile(source, "<host-command>", "exec", dont_inherit=True)
    except (SyntaxError, ValueError) as exc:
        # Do not disclose the source line or arbitrary exception text.
        line = getattr(exc, "lineno", None)
        raise ValueError("HOST_COMMAND_PYTHON_SYNTAX_INVALID" +
                         (f":line={line}" if type(line) is int else "")) from None


def validate_command(command):
    if not isinstance(command, str) or not command.strip() or "\x00" in command:
        raise ValueError("HOST_COMMAND_TEXT_INVALID")
    environment = {k: v for k, v in os.environ.items()
                   if k not in {"BASH_ENV", "ENV", "SHELLOPTS", "BASHOPTS"}}
    try:
        result = subprocess.run(["/bin/bash", "--noprofile", "--norc", "-n"],
                                input=command, text=True, capture_output=True,
                                timeout=5, check=False, env=environment)
    except (OSError, subprocess.TimeoutExpired):
        raise ValueError("HOST_COMMAND_SYNTAX_CHECK_UNAVAILABLE") from None
    # Bash can return 0 for an unterminated heredoc while swallowing subsequent
    # commands as data. Treat that known parser warning as invalid input.
    if result.returncode or ("here-document" in result.stderr and
                             "delimited by end-of-file" in result.stderr):
        raise ValueError("HOST_COMMAND_SHELL_SYNTAX_INVALID")
    lines, cursor, checked, unchecked = command.splitlines(keepends=True), 0, 0, 0
    while cursor < len(lines):
        opener = HEREDOC.fullmatch(lines[cursor].rstrip("\r\n"))
        cursor += 1
        if not opener:
            continue
        # Multiple redirects/compound commands require a full shell parser;
        # do not misinterpret their data or pretend complete Python coverage.
        if "<<" in opener["argv"]:
            break
        try:
            argv = shlex.split(opener["argv"])
        except ValueError:
            break
        delimiter = opener["quoted"] or opener["plain"]
        body = []
        while cursor < len(lines):
            line = lines[cursor]
            cursor += 1
            actual = line.lstrip("\t") if opener["tabs"] else line
            if actual.rstrip("\r\n") == delimiter:
                break
            body.append(actual)
        if argv and PYTHON.fullmatch(argv[0]) and "-" in argv[1:]:
            if opener["quote"]:
                check_python("".join(body))
                checked += 1
            else:
                unchecked += 1  # Shell expansion may change this Python body.
    return {"command_sha256": hashlib.sha256(command.encode()).hexdigest(),
            "shell_syntax_checked": True, "python_blocks_checked": checked,
            "python_blocks_unchecked": unchecked,
            "python_parser_version": sys.version.split()[0],
            "python_coverage": "RECOGNIZED_LITERAL_HEREDOCS_ONLY",
            "syntax_only": True, "dispatch_authorized": False}


def python_command(source):
    check_python(source)
    delimiter = "GACE_PY_" + hashlib.sha256(source.encode()).hexdigest()[:16]
    while delimiter in source.splitlines():
        delimiter += "_"
    return "python3 - <<'" + delimiter + "'\n" + source + (
        "" if source.endswith("\n") else "\n") + delimiter + "\n"


def assemble_request(draft, command_file, output_directory, language):
    try:
        from scripts.chatgpt_isolated_request_select import prepare_data
    except ModuleNotFoundError:
        from chatgpt_isolated_request_select import prepare_data
    directory = Path(output_directory)
    if (not directory.is_dir() or directory.is_symlink()
            or directory.name != "chat-host-requests" or directory.parent.name != ".github"):
        raise ValueError("REQUEST_OUTPUT_DIRECTORY_INVALID")
    data = json.loads(Path(draft).read_text(encoding="utf-8"))
    if (not isinstance(data, dict) or not isinstance(data.get("bounded_host_request"), dict)
            or data["bounded_host_request"].get("command_id") != "host.command"):
        raise ValueError("REQUEST_COMMAND_KIND_INVALID")
    source = Path(command_file).read_text(encoding="utf-8")
    if language not in {"python", "bash"}:
        raise ValueError("COMMAND_LANGUAGE_INVALID")
    command = python_command(source) if language == "python" else source
    data["bounded_host_request"]["command"] = command
    # Validate with the actual selector, but retain source_context as a planning
    # input. Only Actions may emit its trusted wrapped/preflight representation.
    evidence = {}
    prepare_data(copy.deepcopy(data), command_diagnostics=evidence)
    encoded = (json.dumps(data, ensure_ascii=False, indent=2) + "\n").encode()
    if len(encoded) > 8192:  # Existing request-file admission, not a new cap.
        raise ValueError("REQUEST_FILE_INVALID")
    path = directory / ("req_" + secrets.token_hex(12) + ".json")
    fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o600)
    try:
        with os.fdopen(fd, "wb") as output:
            output.write(encoded)
    except BaseException:
        path.unlink(missing_ok=True)
        raise
    return {"request_file": str(path), "request_bytes": len(encoded),
            "authored_command_sha256": hashlib.sha256(command.encode()).hexdigest(), **evidence}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--command-file", type=Path, required=True)
    parser.add_argument("--language", choices=("python", "bash"), default="bash")
    parser.add_argument("--request-draft", type=Path)
    parser.add_argument("--output-directory", type=Path)
    args = parser.parse_args()
    if bool(args.request_draft) != bool(args.output_directory):
        parser.error("request-draft and output-directory must be supplied together")
    try:
        if args.request_draft:
            result = assemble_request(args.request_draft, args.command_file,
                                      args.output_directory, args.language)
        else:
            source = args.command_file.read_text(encoding="utf-8")
            result = validate_command(python_command(source) if args.language == "python" else source)
        print(json.dumps(result, sort_keys=True))
    except (ValueError, TypeError, AttributeError, OSError) as exc:
        print("HOST_COMMAND_PREPARE=FAILED")
        # Only allow fixed diagnostic codes, never command text or source lines.
        code = str(exc)
        if re.fullmatch(r"[A-Z][A-Z_]{1,100}(?::line=\d+)?", code):
            print("HOST_COMMAND_PREPARE_ERROR=" + code)
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
