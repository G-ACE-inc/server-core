#!/usr/bin/env python3
"""Filter code-expression false positives out of the secret-pattern guard.

The scan stays enabled for the whole repository. A match is ignored only when
the assigned value is a programming expression:

- a dotted identifier chain, such as ``fs.readFileSync`` or
  ``process.env.BOT_TOKEN_FILE``, when the next character is ``(``, ``)``,
  or ``?`` and no segment is a long digit-bearing token
- a bare identifier immediately followed by ``(`` (a function call)

Literal credentials, passphrases, hyphenated keys, and JWT-like dotted values
remain failures. Unparseable input fails closed.
"""

import re
import sys

PATTERN = re.compile(
    r"(api[_-]?key|secret|token|password|credential|session)"
    r"[A-Za-z0-9_ -]*[:=]\s*[\"']?[A-Za-z0-9_./+=-]{12,}",
    re.IGNORECASE,
)
IDENT = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\Z")
DOTTED = re.compile(r"[A-Za-z_][A-Za-z0-9_]*(?:\.[A-Za-z_][A-Za-z0-9_]*)+\Z")
CODE_FOLLOWING = frozenset("()?")


def assigned_value(match):
    separator = re.search(r"[:=]\s*(.*)\Z", match.group(0))
    value = separator.group(1)
    if value[:1] in "\"'":
        value = value[1:]
    return value


def is_code_expression(value, following):
    if DOTTED.fullmatch(value):
        if following not in CODE_FOLLOWING:
            return False
        for segment in value.split("."):
            if len(segment) >= 16 and any(character.isdigit() for character in segment):
                return False
        return True
    return bool(IDENT.fullmatch(value) and following == "(")


def classify_grep_line(line):
    """Return ``code``, ``literal``, or ``unparsed`` for one ``git grep`` line."""
    parsed = re.match(r"([^:]+):(\d+):(.*)\Z", line)
    if not parsed:
        return "unparsed"
    content = parsed.group(3)
    matches = list(PATTERN.finditer(content))
    if not matches:
        return "unparsed"
    for match in matches:
        following = content[match.end():match.end() + 1]
        if not is_code_expression(assigned_value(match), following):
            return "literal"
    return "code"


def real_hit_locations(lines):
    locations = []
    for raw in lines:
        line = raw.rstrip("\n")
        if not line.strip():
            continue
        kind = classify_grep_line(line)
        if kind == "code":
            continue
        parsed = re.match(r"([^:]+):(\d+):", line)
        if parsed:
            locations.append(parsed.group(1) + ":" + parsed.group(2) + ":" + kind)
        else:
            locations.append("unparsed")
    return locations


def main(argv=None):
    locations = real_hit_locations(sys.stdin.read().splitlines())
    if locations:
        print("\n".join(locations))
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
