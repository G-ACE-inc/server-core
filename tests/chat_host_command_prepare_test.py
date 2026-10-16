import copy
import io
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))

from scripts import chat_host_command_prepare as author
from scripts.chatgpt_isolated_request_select import prepare, select
from scripts import servercore_bounded_host_gateway_send as sender
from scripts import servercore_bounded_host_receiver as receiver

SHA = "a" * 40
DRAFT = {"bounded_host_request": {"enabled": True, "command_id": "host.command",
          "repository": "G-ACE-inc/server-core", "expected_sha": SHA, "repo_sha": SHA},
         "chat_decision_checkpoint": {"phase": "START"},
         "gitops_request": {"enabled": False}, "source_reflect_request": {"enabled": False}}


class CommandQualityTests(unittest.TestCase):
    def test_python_quoting_unicode_dollars_and_backticks_survive_actual_transport(self):
        source = '''print("apostrophe ' / quotes \\\" / 日本語 / $HOME / `echo danger`")\n'''
        command = author.python_command(source)
        report = author.validate_command(command)
        self.assertEqual(report["python_blocks_checked"], 1)
        contract = {"allowed_command_ids": ["host.command"], "request_schema": "test.host/v1"}
        sent = sender.validate_cli("host.command", SHA, contract,
            repository="G-ACE-inc/server-core", repo_sha=SHA, host_command=command)
        self.assertEqual(receiver.validate_request(sent, contract)["command"], command)

    def test_nonexecuting_checks_never_run_shell_or_python_side_effects(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory, "MUST_NOT_EXIST")
            author.validate_command("touch " + str(marker))
            author.validate_command("printf '%s' \"$(touch " + str(marker) + ")\"")
            author.validate_command(author.python_command(
                "from pathlib import Path\nPath(" + repr(str(marker)) + ").touch()\n"))
            self.assertFalse(marker.exists())

    def test_known_benign_generated_python_executes_with_exact_literal_output(self):
        text = "quotes ' \" 日本語 $HOME `uname` \\ newline\n"
        command = author.python_command("print(" + repr(text) + ", end='')\n")
        result = subprocess.run(["/bin/bash", "--noprofile", "--norc"],
            input=command, text=True, capture_output=True, timeout=5,
            env={"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "LANG": "C.UTF-8"})
        self.assertEqual(result.returncode, 0)
        self.assertEqual(result.stdout, text)

    def test_generated_python_syntax_errors_rejected_before_request_or_execution(self):
        for source in ("print('unterminated)", "print('x'", "print('x'))", "if True\n pass", "return 1"):
            with self.subTest(source=source), self.assertRaisesRegex(
                    ValueError, "HOST_COMMAND_PYTHON_SYNTAX_INVALID"):
                author.python_command(source)

    def test_existing_literal_python_heredoc_checked_and_error_text_does_not_leak(self):
        with self.assertRaisesRegex(ValueError, "HOST_COMMAND_PYTHON_SYNTAX_INVALID") as error:
            author.validate_command("python3 - <<'PY'\nprint('private-sentinel)\nPY\n")
        self.assertNotIn("private-sentinel", str(error.exception))
        self.assertEqual(author.validate_command("python3 - <<\"PY\"\nprint('ok')\nPY\n")["python_blocks_checked"], 1)

    def test_bash_syntax_and_missing_heredoc_terminator_rejected(self):
        for command in ("printf 'unterminated", "if true; then echo ok", "cat <<'END'\nbody\n"):
            with self.subTest(command=command), self.assertRaisesRegex(
                    ValueError, "HOST_COMMAND_SHELL_SYNTAX_INVALID"):
                author.validate_command(command)

    def test_other_heredoc_data_is_not_mistaken_for_executable_python(self):
        command = "cat <<'TEXT'\npython3 - <<'PY'\ninvalid python ' here\nPY\nTEXT\nprintf ok\n"
        self.assertEqual(author.validate_command(command)["python_blocks_checked"], 0)

    def test_dynamic_python_body_is_explicitly_unchecked(self):
        result = author.validate_command("python3 - <<PY\n$GENERATED_CODE\nPY\n")
        self.assertEqual((result["python_blocks_checked"], result["python_blocks_unchecked"]), (0, 1))
        self.assertEqual(result["python_coverage"], "RECOGNIZED_LITERAL_HEREDOCS_ONLY")

    def test_tab_stripped_heredoc_validated_as_bash_will_supply_it(self):
        self.assertEqual(author.validate_command("python3 - <<-'PY'\n\tprint('ok')\n\tPY\n")["python_blocks_checked"], 1)

    def test_request_assembly_uses_unique_compliant_names_and_same_selector(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / ".github/chat-host-requests"
            output.mkdir(parents=True)
            draft, source = root / "draft.json", root / "command.py"
            draft.write_text(json.dumps(DRAFT))
            source.write_text("print('日本語')\n")
            first = author.assemble_request(draft, source, output, "python")
            second = author.assemble_request(draft, source, output, "python")
            self.assertNotEqual(first["request_file"], second["request_file"])
            file = Path(first["request_file"])
            relative = ".github/chat-host-requests/" + file.name
            self.assertEqual(select([relative], [relative]), Path(relative))
            self.assertTrue(re.fullmatch(r"req_[a-f0-9]{24}\.json", file.name))
            self.assertEqual(prepare(file)["bounded_host_request"]["command"], author.python_command(source.read_text()))
            self.assertFalse(first["dispatch_authorized"])
            self.assertNotIn("print", json.dumps(first))
            self.assertEqual(json.loads(draft.read_text()), DRAFT)

    def test_selector_rejects_bad_commands_without_author_helper(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory, "request.json")
            for command in ("echo 'unfinished", "python3 - <<'PY'\nprint('x'\nPY\n"):
                request = copy.deepcopy(DRAFT)
                request["bounded_host_request"]["command"] = command
                path.write_text(json.dumps(request))
                with self.assertRaisesRegex(ValueError, "HOST_COMMAND_.*SYNTAX_INVALID"):
                    prepare(path)

    def test_invalid_draft_does_not_forge_start_or_write_requests(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / ".github/chat-host-requests"
            output.mkdir(parents=True)
            draft, source = root / "draft.json", root / "command.py"
            draft.write_text(json.dumps({**DRAFT, "chat_decision_checkpoint": {}}))
            source.write_text("print('ok')")
            with self.assertRaisesRegex(ValueError, "START_RECEIPT_MISSING"):
                author.assemble_request(draft, source, output, "python")
            self.assertEqual(list(output.iterdir()), [])

    def test_existing_request_file_limit_is_checked_before_creating_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / ".github/chat-host-requests"
            output.mkdir(parents=True)
            draft, source = root / "draft.json", root / "large.sh"
            draft.write_text(json.dumps(DRAFT)); source.write_text("#" + "x" * 9000)
            with self.assertRaisesRegex(ValueError, "REQUEST_FILE_INVALID"):
                author.assemble_request(draft, source, output, "bash")
            self.assertEqual(list(output.iterdir()), [])

    def test_source_context_remains_input_not_trusted_preflight_output(self):
        data = copy.deepcopy(DRAFT)
        data["bounded_host_request"]["source_context"] = {
            "repository": "G-ACE-inc/server-core", "workdir": "/home/admin1/server-core",
            "source_sha": SHA, "required_files": ["README.md"]}
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            output = root / ".github/chat-host-requests"
            output.mkdir(parents=True)
            draft, source = root / "draft.json", root / "command.py"
            draft.write_text(json.dumps(data)); source.write_text("print('ok')")
            result = author.assemble_request(draft, source, output, "python")
            written = json.loads(Path(result["request_file"]).read_text())["bounded_host_request"]
            self.assertIn("source_context", written)
            self.assertNotIn("source_preflight", written)
            self.assertTrue(prepare(Path(result["request_file"]))["bounded_host_request"]["source_preflight"])

    def test_parser_environment_startup_file_is_not_executed(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory, "MUST_NOT_EXIST")
            startup = Path(directory, "startup.sh")
            startup.write_text("touch " + str(marker))
            with patch.dict("os.environ", {"BASH_ENV": str(startup)}):
                author.validate_command("echo ok")
            self.assertFalse(marker.exists())

    def test_cli_diagnostic_contains_code_not_source(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory, "bad.py")
            source.write_text("print('private-sentinel)")
            captured = io.StringIO()
            with patch("sys.argv", ["prepare", "--command-file", str(source), "--language", "python"]), redirect_stdout(captured):
                with self.assertRaises(SystemExit):
                    author.main()
            self.assertIn("HOST_COMMAND_PYTHON_SYNTAX_INVALID", captured.getvalue())
            self.assertNotIn("private-sentinel", captured.getvalue())


if __name__ == "__main__":
    unittest.main()
