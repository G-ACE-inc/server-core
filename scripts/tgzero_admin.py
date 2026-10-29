#!/usr/bin/env python3
"""Route TGserver ZERO administration to its owning repository; no second registry."""
import argparse
import json
import os
import pathlib
import re
import subprocess
import sys

CONTRACT = json.loads((pathlib.Path(__file__).resolve().parents[1] / 'operations/tgzero-registration.json').read_text())
DEFAULT_OWNER = pathlib.Path(CONTRACT['runtime_checkout'])


def command_args(args):
    root = args.tgserver_root.resolve(strict=True)
    script = root / 'scripts/project-register.js'
    if not script.is_file():
        raise ValueError('TGSERVER_REGISTRATION_TOOL_NOT_INSTALLED')
    if args.action in ('register', 'register-group', 'reflect', 'runtime-status'):
        owner = root / 'scripts/registration-admin.py'
        if not owner.is_file():
            raise ValueError('TGSERVER_WORKFLOW_NOT_INSTALLED')
        command = ['python3', str(owner), args.action, '--root', str(root)]
        for key in ('request', 'operation_dir', 'image'):
            value = getattr(args, key, None)
            if value is not None:
                command += ['--' + key.replace('_', '-'), str(value)]
        if getattr(args, 'dry_run', False):
            command += ['--dry-run']
        return command
    if args.action in ('audit-topics', 'provision'):
        if args.action == 'provision' and (not args.project or not re.fullmatch(r'P\d{3}', args.project) or
                not args.state_sha256 or not re.fullmatch(r'[a-f0-9]{64}', args.state_sha256)):
            raise ValueError('PROVISION_REQUIRES_SINGLE_PROJECT_AND_LIVE_STATE_SHA256')
        if (root / '.tgs-state/registration-transaction.json').exists():
            raise ValueError('RECOVER_PENDING_TRANSACTION_FIRST')
        # Reuse dependencies from the actual running ZERO image, not another Bot client.
        image = json.loads(subprocess.check_output(
            ['docker', 'inspect', '--format', '{{json .Image}}', 'tgserver-tgs-1'], text=True))
        if not re.fullmatch(r'sha256:[a-f0-9]{64}', image):
            raise ValueError('VERIFIED_RUNTIME_IMAGE_REQUIRED')
        command = ['docker', 'run', '--rm', '--read-only', '--cap-drop=ALL',
                   '--security-opt=no-new-privileges', '--user', f'{os.getuid()}:{os.getgid()}',
                   '-v', f'{root}:/owner' + (':ro' if args.action == 'audit-topics' else ''),
                   '-w', '/owner', '-e', 'NODE_PATH=/app/node_modules', '-e', 'TS_NODE_TRANSPILE_ONLY=1',
                   '--entrypoint', 'node', image, '-r', '/app/node_modules/ts-node/register',
                   '/owner/scripts/topics-provision.ts']
        if args.action == 'audit-topics':
            command[3:3] = ['--network=none']
            command += ['--audit']
        else:
            command += ['--project', args.project, '--confirm-live-state', '--baseline-sha256', args.state_sha256]
        return command
    # Mount private request/plan directory separately, never interpolate shell text.
    command = ['docker', 'run', '--rm', '--network=none', '--user',
               f'{os.getuid()}:{os.getgid()}',
               '--read-only', '--cap-drop=ALL', '--security-opt=no-new-privileges',
               '-v', f'{root}:/owner' + (':ro' if args.action in ('status', 'lookup', 'plan-project', 'plan-group') else '')]
    owner_args = [args.action, '--root', '/owner']
    if args.action == 'lookup':
        if not getattr(args, 'repo', None) and not args.project:
            raise ValueError('REPO_OR_PROJECT_REQUIRED')
        for key in ('repo', 'stream', 'project'):
            value = getattr(args, key, None)
            if value is not None:
                owner_args += ['--' + key, value]
    if args.action in ('plan-project', 'plan-group', 'apply'):
        if args.plan is None:
            raise ValueError('PRIVATE_PLAN_PATH_REQUIRED')
        plan = args.plan.absolute()
        private_dir = plan.parent.resolve(strict=True)
        if private_dir == root or private_dir.is_relative_to(root):
            raise ValueError('KEEP_PLANS_OUTSIDE_GIT_WORKTREE')
        if private_dir.stat().st_mode & 0o077:
            raise ValueError('PLAN_DIRECTORY_REQUIRES_MODE_700')
        command += ['-v', f'{private_dir}:/private']
        owner_args += ['--plan', '/private/' + plan.name]
        if args.action.startswith('plan-'):
            if args.request is None:
                raise ValueError('PRIVATE_REQUEST_PATH_REQUIRED')
            request = args.request.resolve(strict=True)
            if request.parent != private_dir:
                raise ValueError('REQUEST_AND_PLAN_MUST_SHARE_PRIVATE_DIRECTORY')
            owner_args += ['--request', '/private/' + request.name]
        else:
            if not args.digest:
                raise ValueError('PLAN_DIGEST_REQUIRED')
            owner_args += ['--digest', args.digest]
    return command + ['node:20-alpine', 'node', '/owner/scripts/project-register.js'] + owner_args


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['status', 'lookup', 'register', 'register-group', 'reflect', 'runtime-status', 'plan-project', 'plan-group', 'apply', 'recover', 'audit-topics', 'provision'])
    parser.add_argument('--tgserver-root', type=pathlib.Path, default=DEFAULT_OWNER)
    parser.add_argument('--request', type=pathlib.Path)
    parser.add_argument('--plan', type=pathlib.Path)
    parser.add_argument('--digest')
    parser.add_argument('--project')
    parser.add_argument('--state-sha256')
    parser.add_argument('--repo')
    parser.add_argument('--stream')
    parser.add_argument('--operation-dir', type=pathlib.Path)
    parser.add_argument('--image')
    parser.add_argument('--dry-run', action='store_true')
    args = parser.parse_args(argv)
    try:
        if args.action == 'lookup':
            result = subprocess.run(command_args(args), capture_output=True, text=True, check=False)
            if result.returncode:
                print(result.stderr, end='', file=sys.stderr)
                return result.returncode
            value = json.loads(result.stdout)
            value['authority'] = {key: str(args.tgserver_root.resolve() / pathlib.PurePosixPath(file).relative_to('/owner'))
                                  for key, file in value['authority'].items()}
            print(json.dumps(value, ensure_ascii=False, indent=2))
            return 0
        return subprocess.run(command_args(args), check=False).returncode
    except (OSError, ValueError) as error:
        print('TGZERO_ADMIN_ERROR=' + (str(error) if isinstance(error, ValueError) else type(error).__name__), file=sys.stderr)
        return 1


if __name__ == '__main__':
    sys.exit(main())
