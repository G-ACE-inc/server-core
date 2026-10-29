#!/usr/bin/env python3
"""Select remote CHAT tests from changed paths; unknown/executable changes use full CI."""
import argparse
import pathlib
import subprocess

PROFILE_PATHS = {'AGENTS.md', '.github/copilot-instructions.md', 'operations/github-project-rule-plane.json',
                 'scripts/workspace_command_center_check.py', 'scripts/workspace_command_center_check_test.py'}


def classify(paths):
    paths = set(paths)
    profile_only = bool(paths) and all(
        path in PROFILE_PATHS or path.endswith('.md') or path.startswith(('.cursor/rules/', '.cursor/templates/'))
        for path in paths)
    return {'profile_only': profile_only, 'remote_chat': not profile_only}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--base', default='')
    parser.add_argument('--output', type=pathlib.Path)
    args = parser.parse_args()
    if not args.base or args.base == '0' * 40:
        result = classify([])  # Manual/initial/unknown scope: preserve full validation.
    else:
        if subprocess.run(['git', 'cat-file', '-e', args.base + '^{commit}'], capture_output=True).returncode:
            subprocess.run(['git', 'fetch', '--quiet', '--no-tags', '--depth=1', 'origin', args.base], check=True)
        paths = subprocess.check_output(['git', 'diff', '--name-only', args.base, 'HEAD'], text=True).splitlines()
        result = classify(paths)
    rendered = ''.join(f'{key}={str(value).lower()}\n' for key, value in result.items())
    print(rendered, end='')
    if args.output:
        with args.output.open('a') as stream:
            stream.write(rendered)


if __name__ == '__main__':
    main()
