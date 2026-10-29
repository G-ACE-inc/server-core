import importlib.util
import pathlib
import tempfile
import unittest
from argparse import Namespace
from unittest.mock import patch

spec = importlib.util.spec_from_file_location('tgzero_admin', pathlib.Path(__file__).with_name('tgzero_admin.py'))
admin = importlib.util.module_from_spec(spec)
spec.loader.exec_module(admin)


class RouterTests(unittest.TestCase):
    def test_owner_delegation_uses_argv_no_shell_and_readonly_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'scripts').mkdir()
            (root / 'scripts/project-register.js').touch()
            args = Namespace(tgserver_root=root, action='status', plan=None, request=None, digest=None)
            command = admin.command_args(args)
            self.assertIn(f'{root}:/owner:ro', command)
            self.assertIn('--network=none', command)
            self.assertEqual(command[-3:], ['status', '--root', '/owner'])

    def test_private_plan_paths_and_literal_arguments(self):
        with tempfile.TemporaryDirectory() as directory, tempfile.TemporaryDirectory() as private:
            root = pathlib.Path(directory)
            (root / 'scripts').mkdir()
            (root / 'scripts/project-register.js').touch()
            request = pathlib.Path(private) / 'request.json'
            request.write_text('{}')
            plan = pathlib.Path(private) / 'plan $(never execute).json'
            args = Namespace(tgserver_root=root, action='plan-project', plan=plan, request=request, digest=None)
            command = admin.command_args(args)
            self.assertIn('/private/' + plan.name, command)
            args.plan = root / 'unsafe.json'
            with self.assertRaisesRegex(ValueError, 'OUTSIDE_GIT'):
                admin.command_args(args)

    def test_provision_reuses_running_image_and_requires_single_project_and_hash(self):
        with tempfile.TemporaryDirectory() as directory:
            root = pathlib.Path(directory)
            (root / 'scripts').mkdir()
            (root / 'scripts/project-register.js').touch()
            args = Namespace(tgserver_root=root, action='provision', project=None, state_sha256=None)
            with self.assertRaisesRegex(ValueError, 'SINGLE_PROJECT'):
                admin.command_args(args)
            args.project, args.state_sha256 = 'P016', 'a' * 64
            with patch.object(admin.subprocess, 'check_output', return_value='"sha256:' + 'b' * 64 + '"'):
                command = admin.command_args(args)
            self.assertIn('/owner/scripts/topics-provision.ts', command)
            self.assertIn('--confirm-live-state', command)
            self.assertIn('sha256:' + 'b' * 64, command)
            self.assertEqual(command[-2:], ['--baseline-sha256', 'a' * 64])
            (root / '.tgs-state').mkdir()
            (root / '.tgs-state/registration-transaction.json').touch()
            with self.assertRaisesRegex(ValueError, 'RECOVER_PENDING'):
                admin.command_args(args)


if __name__ == '__main__':
    unittest.main()
