"""Isolated development terminal (design 16.11): provisioner admission, sandbox shape, Receiver and sender wiring."""
import fcntl
import importlib.util
import json
import os
from pathlib import Path
import shutil
import socketserver
import subprocess
import sys
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))


def load(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


job = load("servercore_dev_job_socket", "servercore_dev_job_socket.py")
receiver = load("servercore_bounded_host_receiver", "servercore_bounded_host_receiver.py")
sender = load("servercore_bounded_host_gateway_send", "servercore_bounded_host_gateway_send.py")

DESIGN = "# D\n\n## 16. X\n\n### 16.11 Current design baseline\n\nBody text.\n\n### 16.12 Next\nunrelated\n"
IMAGE = "img:test"


def run_git(root, *args):
    subprocess.run(["git", "-c", "user.name=t", "-c", "user.email=t@t", "-C", str(root), *args],
                   check=True, capture_output=True)


def head(root):
    return subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True, capture_output=True,
                          text=True).stdout.strip()


class Fake:
    """Replaces run_bounded: records every docker argv; no Docker is executed."""

    def __init__(self, exit_code=0, sha="0" * 40):
        self.calls, self.exit_code, self.sha = [], exit_code, sha

    def __call__(self, cmd, timeout, kill):
        self.calls.append(cmd)
        full = [cmd[cmd.index("--entrypoint") + 1]] + cmd[cmd.index(IMAGE) + 1:]
        if full[:2] == ["git", "rev-parse"]:
            return 0, (self.sha + "\n").encode(), b"", False, False
        if full[:2] == ["git", "status"]:
            return 0, b" M README.md\n", b"", False, False
        if full[:2] == ["git", "diff"]:
            return 0, b" 1 file changed, 1 insertion(+)\n", b"", False, False
        return self.exit_code, b"job-out", b"job-err", False, False


class Base(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, self.tmp, True)
        self.root = self.tmp / "server-core"
        self.root.mkdir()
        self.state = self.tmp / "state"
        run_git(self.root, "init", "-q", "-b", "main")
        (self.root / "README.md").write_text("hello\n")
        (self.root / "docs").mkdir()
        (self.root / "docs/SERVER_CORE_DESIGN.md").write_text(DESIGN)
        (self.root / "operations").mkdir()
        self.write_contract()
        self.commit()
        self.sid = "req_" + "a" * 24
        self.fake = Fake(sha=head(self.root))

    def write_contract(self, executables=("git", "python3", "sh"), design=DESIGN):
        contract = {
            "allowed_command_ids": ["dev.job"], "command_effects": {"dev.job": "dev_job"},
            "dev_job": {"image": IMAGE, "design_section_sha256": job.design_section_digest(design),
                        "allowed_executables": list(executables),
                        "registered_repositories": {"G-ACE-inc/server-core": {
                            "owner": "G-ACE-inc", "root": str(self.root), "branch": "main", "project_item": "P1"}}}}
        (self.root / "operations/github-project-bounded-host.json").write_text(json.dumps(contract))

    def commit(self):
        run_git(self.root, "add", "-A")
        run_git(self.root, "commit", "-q", "-m", "c")

    def request(self, **over):
        value = {"schema": job.SCHEMA, "id": "req_" + os.urandom(12).hex(), "repository": "G-ACE-inc/server-core",
                 "expected_sha": head(self.root), "session": self.sid, "argv": ["git", "status"],
                 "timeout_s": 5, "fresh": False}
        value.update(over)
        return value

    def go(self, value=None, runner=None, **kwargs):
        return job.handle_request(value or self.request(), root=self.root, state_dir=self.state, binary="/usr/bin/docker",
                                  runner=runner or self.fake, **kwargs)

    def denied(self, code, value=None, **kwargs):
        before = len(self.fake.calls)
        with self.assertRaises(job.JobError) as ctx:
            self.go(value, **kwargs)
        self.assertEqual(str(ctx.exception), code)
        self.assertEqual(len(self.fake.calls), before, "denied request must not start a container")


class ProvisionerPositive(Base):
    def test_sandbox_shape_is_fixed_and_minimal(self):
        result = self.go(self.request(argv=["python3", "-c", "print(1)"]))
        cmd = self.fake.calls[0]
        workspace = str(self.root / ".worktrees/dev-jobs" / self.sid)
        for flag in ("--rm", "--read-only"):
            self.assertIn(flag, cmd)
        self.assertEqual(cmd[cmd.index("--network") + 1], "none")
        self.assertEqual(cmd[cmd.index("--cap-drop") + 1], "ALL")
        self.assertEqual(cmd[cmd.index("--user") + 1], "1000:1000")
        self.assertEqual(cmd[cmd.index("--pull") + 1], "never")
        self.assertIn("no-new-privileges:true", cmd)
        self.assertEqual(cmd.count("--mount"), 1)
        self.assertEqual(cmd[cmd.index("--mount") + 1], "type=bind,src=%s,dst=/work" % workspace)
        flat = " ".join(cmd)
        for forbidden in ("docker.sock", "--privileged", "--volume", " -v ", "--env-file", "--network host", "/run/secrets"):
            self.assertNotIn(forbidden, flat)
        self.assertEqual(result["job_exit"], 0)
        self.assertEqual(result["stdout"], "job-out")
        self.assertEqual(result["changed"], [" M README.md"])
        self.assertEqual(result["project_item"], "P1")
        self.assertEqual(result["base_sha"], head(self.root))
        self.assertTrue((Path(workspace) / "README.md").is_file())  # real clone + checkout of the commit
        self.assertFalse((Path(workspace) / "operations/master-internal-repositories.json").exists())

    def test_workspace_is_clone_of_commit_not_dirty_working_tree(self):
        (self.root / "README.md").write_text("DIRTY HOST BYTES\n")
        self.go()
        self.assertEqual((self.root / ".worktrees/dev-jobs" / self.sid / "README.md").read_text(), "hello\n")

    def test_failing_job_is_reported_not_raised_and_retry_in_same_session_reuses_workspace(self):
        failing = Fake(exit_code=3, sha=head(self.root))
        first = self.go(self.request(argv=["python3", "-c", "raise SystemExit(3)"]), runner=failing)
        self.assertEqual(first["job_exit"], 3)
        workspace = self.root / ".worktrees/dev-jobs" / self.sid
        (workspace / "marker.txt").write_text("kept")
        second = self.go(self.request(argv=["git", "status"]))
        self.assertEqual(second["job_exit"], 0)
        self.assertTrue((workspace / "marker.txt").exists())
        third = self.go(self.request(fresh=True))
        self.assertFalse((workspace / "marker.txt").exists())
        self.assertEqual(third["job_exit"], 0)

    def test_diff_stdout_is_bounded_and_no_git_remote_is_available(self):
        """The sandbox can return a small diff, but its result is not a GitHub promotion."""
        patch_text = "diff --git a/README.md b/README.md\n+added line\n"

        class DiffFake(Fake):
            def __call__(self, cmd, timeout, kill):
                args = [cmd[cmd.index("--entrypoint") + 1]] + cmd[cmd.index(IMAGE) + 1:]
                if args[:2] == ["git", "diff"] and "--shortstat" not in args:
                    self.calls.append(cmd)
                    return 0, patch_text.encode(), b"", False, False
                return super().__call__(cmd, timeout, kill)

        runner = DiffFake(sha=head(self.root))
        result = self.go(self.request(argv=["git", "diff", "--", "README.md"]), runner=runner)
        self.assertEqual(result["stdout"], patch_text)
        self.assertFalse(result["stdout_truncated"])
        self.assertFalse(result["stderr_truncated"])
        self.assertEqual(result["changed"], [" M README.md"])
        workspace = self.root / ".worktrees/dev-jobs" / self.sid
        remotes = subprocess.run(["git", "-C", str(workspace), "remote"], capture_output=True, text=True, check=True)
        self.assertEqual(remotes.stdout, "")
        self.assertLessEqual(len(result["stdout"]), job.RESULT_CHARS)

    def test_diff_output_limit_is_not_a_complete_patch_guarantee(self):
        """Never promote a patch that is only a tail of an oversized stdout."""
        self.assertEqual(job._text(b"x" * (job.RESULT_CHARS + 10)), "x" * job.RESULT_CHARS)

        class OversizedFake(Fake):
            def __call__(self, cmd, timeout, kill):
                args = [cmd[cmd.index("--entrypoint") + 1]] + cmd[cmd.index(IMAGE) + 1:]
                if args[:2] == ["git", "diff"] and "--shortstat" not in args:
                    self.calls.append(cmd)
                    return 0, b"x" * (job.RESULT_CHARS + 10), b"", False, False
                return super().__call__(cmd, timeout, kill)

        result = self.go(self.request(argv=["git", "diff", "--", "README.md"]),
                         runner=OversizedFake(sha=head(self.root)))
        self.assertTrue(result["stdout_truncated"])
        self.assertFalse(result["stderr_truncated"])
        self.assertEqual(len(result["stdout"]), job.RESULT_CHARS)

    def test_records_are_private(self):
        value = self.request()
        self.go(value)
        mode = (self.state / (value["id"] + ".json")).stat().st_mode & 0o777
        self.assertEqual(mode, 0o600)
        self.assertEqual(self.state.stat().st_mode & 0o777, 0o700)


class ProvisionerNegative(Base):
    def test_unregistered_and_wrong_owner_repository(self):
        self.denied("REPOSITORY_NOT_REGISTERED", self.request(repository="G-ACE-inc/other"))
        self.denied("REPOSITORY_NOT_REGISTERED", self.request(repository="evil/server-core"))
        self.denied("REPOSITORY_INVALID", self.request(repository="../x"))

    def test_shape_rejects_unknown_fields_such_as_mounts(self):
        self.denied("REQUEST_SHAPE_INVALID", self.request(mounts=["/var/run/docker.sock:/var/run/docker.sock"]))
        value = self.request()
        del value["fresh"]
        self.denied("REQUEST_SHAPE_INVALID", value)
        self.denied("REQUEST_SHAPE_INVALID", self.request(schema="other"))

    def test_executable_allowlist_and_argv_bounds(self):
        for argv in (["rm", "-rf", "/"], ["bash", "-c", "x"], ["/bin/sh", "-c", "x"], ["docker", "ps"], ["../git"]):
            self.denied("EXECUTABLE_NOT_ALLOWED", self.request(argv=argv))
        self.denied("ARGV_INVALID", self.request(argv=[]))
        self.denied("ARGV_INVALID", self.request(argv=["git"] + ["x"] * 8))
        self.denied("ARGV_INVALID", self.request(argv=["git", "x" * 1300]))
        self.denied("ARGV_INVALID", self.request(argv=["git", "a\x00b"]))
        self.denied("ARGV_INVALID", self.request(argv=["python3", "-c", "x" * 1100, "y" * 1100, "z" * 400]))
        self.denied("ARGV_INVALID", self.request(argv="git status"))
        self.denied("TIMEOUT_INVALID", self.request(timeout_s=0))
        self.denied("TIMEOUT_INVALID", self.request(timeout_s=job.MAX_TIMEOUT + 1))
        self.denied("TIMEOUT_INVALID", self.request(timeout_s=True))
        self.denied("FRESH_INVALID", self.request(fresh="yes"))
        self.denied("SESSION_INVALID", self.request(session="../../etc"))
        self.denied("SESSION_INVALID", self.request(session="req_" + "A" * 24))
        self.denied("EXPECTED_SHA_INVALID", self.request(expected_sha="HEAD"))

    def test_uncommitted_contract_widening_is_ignored(self):
        self.write_contract(executables=("git", "python3", "sh", "bash"))  # working tree only, not committed
        self.denied("EXECUTABLE_NOT_ALLOWED", self.request(argv=["bash", "-c", "id"]))

    def test_stale_sha(self):
        self.denied("STALE_SHA", self.request(expected_sha="b" * 40))

    def test_branch_must_match_registry(self):
        run_git(self.root, "checkout", "-q", "-b", "feature")
        self.denied("BRANCH_NOT_REGISTERED", self.request())

    def test_detached_head_at_registered_branch_tip_is_allowed(self):
        run_git(self.root, "checkout", "-q", "--detach", "HEAD")
        self.assertEqual(self.go(self.request())["job_exit"], 0)

    def test_design_digest_missing_stale_or_modified(self):
        (self.root / "docs/SERVER_CORE_DESIGN.md").write_text(DESIGN.replace("Body text.", "Widened acceptance."))
        self.commit()
        self.denied("DESIGN_NOT_VERIFIED", self.request())
        (self.root / "docs/SERVER_CORE_DESIGN.md").write_text("# D\n\n## 16. X\n")
        self.commit()
        self.denied("DESIGN_NOT_VERIFIED", self.request())

    def test_design_change_with_matching_contract_digest_is_accepted_only_when_both_committed(self):
        changed = DESIGN.replace("Body text.", "Reviewed change.")
        (self.root / "docs/SERVER_CORE_DESIGN.md").write_text(changed)
        self.write_contract(design=changed)
        self.commit()
        self.assertEqual(self.go(self.request())["job_exit"], 0)

    def test_symlinked_worktrees_parent_is_denied_and_nothing_created_outside(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        os.symlink(outside, self.root / ".worktrees")
        self.denied("WORKSPACE_PATH_SYMLINK_DENIED")
        self.assertEqual(list(outside.iterdir()), [])

    def test_symlinked_dev_jobs_and_session_path_are_denied(self):
        outside = self.tmp / "outside"
        outside.mkdir()
        (self.root / ".worktrees").mkdir()
        os.symlink(outside, self.root / ".worktrees/dev-jobs")
        self.denied("WORKSPACE_PATH_SYMLINK_DENIED")
        os.unlink(self.root / ".worktrees/dev-jobs")
        (self.root / ".worktrees/dev-jobs").mkdir()
        os.symlink(outside, self.root / ".worktrees/dev-jobs" / self.sid)
        self.denied("WORKSPACE_PATH_SYMLINK_DENIED")
        self.assertEqual(list(outside.iterdir()), [])

    def test_registered_root_must_be_real_and_not_sibling(self):
        entry = {"root": str(self.tmp / "nope")}
        with self.assertRaises(job.JobError):
            job.check_registered_root(entry, self.root)
        link = self.tmp / "link"
        os.symlink(self.root, link)
        with self.assertRaises(job.JobError):
            job.check_registered_root({"root": str(link)}, self.root)
        with self.assertRaises(job.JobError):  # real git repo but neither the canonical root nor under projects/
            sibling = self.tmp / "sibling"
            (sibling / ".git").mkdir(parents=True)
            job.check_registered_root({"root": str(sibling)}, self.root)

    def test_replay_returns_stored_result_without_reexecution(self):
        value = self.request()
        first = self.go(value)
        calls = len(self.fake.calls)
        again = self.go(value)
        self.assertEqual(len(self.fake.calls), calls)
        self.assertTrue(again["replayed"])
        self.assertEqual(again["stdout"], first["stdout"])

    def test_conflicting_writer_in_same_session_is_busy(self):
        self.go()
        _, _, lock_path = job.state_paths(self.state, "req_" + "c" * 24, self.sid)
        fd = os.open(lock_path, os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.denied("DEV_JOB_BUSY", self.request())

    def test_session_base_mismatch_requires_fresh(self):
        self.go()
        (self.root / "README.md").write_text("v2\n")
        self.commit()
        self.fake.sha = head(self.root)
        self.denied("SESSION_BASE_MISMATCH", self.request())
        self.assertEqual(self.go(self.request(fresh=True))["job_exit"], 0)
        self.assertEqual((self.root / ".worktrees/dev-jobs" / self.sid / "README.md").read_text(), "v2\n")

    def test_session_limit(self):
        base = job.workspace_base(self.root)
        for i in range(job.MAX_SESSIONS):
            (base / ("req_%024x" % i)).mkdir()
        self.denied("SESSION_LIMIT_REACHED", self.request(session="req_" + "e" * 24))

    def test_workspace_budget_exceeded_discards_workspace(self):
        with patch.object(job, "WORKSPACE_BYTES", 10):
            result = self.go()
        self.assertTrue(result["workspace_budget_exceeded"])
        self.assertFalse((self.root / ".worktrees/dev-jobs" / self.sid).exists())

    def test_workspace_create_failure_is_cleaned(self):
        def broken(root, workspace, sha):
            workspace.mkdir()
            raise job.JobError("WORKSPACE_CREATE_FAILED")
        with self.assertRaises(job.JobError):
            self.go(clone=broken)

    def test_collection_failure_reports_unknown_not_crash(self):
        def collect_fails(cmd, timeout, kill):
            self.fake.calls.append(cmd)
            full = cmd[cmd.index(IMAGE) + 1:]
            return (0, b"x", b"", False, False) if cmd[cmd.index("--entrypoint") + 1] == "python3" else (1, b"", b"e", False, False)
        result = self.go(self.request(argv=["python3", "-c", "1"]), runner=collect_fails)
        self.assertEqual(result["workspace_head"], "UNKNOWN")
        self.assertEqual(result["changed"], [])


class BoundedRunner(unittest.TestCase):
    def test_wall_clock_timeout_kills(self):
        started = time.monotonic()
        rc, _, _, timed_out, _ = job.run_bounded(["sleep", "10"], 1)
        self.assertTrue(timed_out)
        self.assertEqual(rc, 124)
        self.assertLess(time.monotonic() - started, 6)

    def test_output_cap_kills_runaway_writer(self):
        rc, out, _, _, exceeded = job.run_bounded([sys.executable, "-c", "import sys\nwhile True: sys.stdout.write('x'*65536)"], 20)
        self.assertTrue(exceeded)
        self.assertLessEqual(len(out), job.CAPTURE_CAP)

    def test_normal_output_and_exit_code(self):
        rc, out, err, timed_out, exceeded = job.run_bounded([sys.executable, "-c", "import sys;print('o');sys.stderr.write('e');sys.exit(4)"], 10)
        self.assertEqual((rc, out.strip(), err, timed_out, exceeded), (4, b"o", b"e", False, False))


class ReceiverWiring(unittest.TestCase):
    CONTRACT = {"request_schema": "gace.servercore-bounded-host.request/v1", "allowed_command_ids": ["dev.job", "project.git_head"]}

    def req(self, **over):
        value = {"schema": self.CONTRACT["request_schema"], "id": "req_" + "1" * 24, "command_id": "dev.job",
                 "expected_sha": "a" * 40, "repository": "G-ACE-inc/server-core", "session": "req_" + "2" * 24,
                 "argv": ["git", "status"], "timeout_s": 5, "fresh": False}
        value.update(over)
        return value

    def test_validate_request_exact_shape(self):
        parsed = receiver.validate_request(self.req(), self.CONTRACT)
        self.assertEqual(parsed["argv"], ["git", "status"])
        for bad in ({"extra": 1}, {"timeout_s": 16}, {"fresh": 1}, {"argv": []}, {"argv": ["x"] * 9},
                    {"session": "s"}, {"repository": "no-slash"}):
            with self.assertRaises(receiver.ReceiverError):
                receiver.validate_request(self.req(**bad), self.CONTRACT)
        value = self.req()
        del value["argv"]
        with self.assertRaises(receiver.ReceiverError):
            receiver.validate_request(value, self.CONTRACT)
        with self.assertRaises(receiver.ReceiverError):  # command not in contract
            receiver.validate_request(self.req(), {**self.CONTRACT, "allowed_command_ids": ["project.git_head"]})

    def test_record_fields_pass_fail_timeout(self):
        base = {"session": "s", "base_sha": "a" * 40, "workspace_head": "a" * 40, "changed": [" M x"] * 30,
                "diff_stat": "d", "duration_ms": 5, "replayed": False, "stdout": "out", "stderr": "err",
                "timed_out": False, "output_limit_exceeded": False, "workspace_budget_exceeded": False}
        state, code, out, err = receiver.dev_job_record_fields({**base, "job_exit": 0})
        self.assertEqual((state, code, err), ("PASS", 0, "err"))
        meta = json.loads(out.split("\n", 1)[0][len("GACE_DEV_JOB "):])
        self.assertEqual(len(meta["changed"]), 10)
        self.assertIn("stdout_truncated", meta)
        self.assertIn("stderr_truncated", meta)
        self.assertTrue(out.endswith("\nout"))
        self.assertEqual(receiver.dev_job_record_fields({**base, "job_exit": 2})[:2], ("FAIL", 2))
        self.assertEqual(receiver.dev_job_record_fields({**base, "job_exit": 0, "timed_out": True})[:2], ("FAIL", 1))
        self.assertEqual(receiver.dev_job_record_fields({**base, "job_exit": 124, "timed_out": True})[:2], ("FAIL", 124))
        self.assertEqual(receiver.dev_job_record_fields({**base, "job_exit": 0, "output_limit_exceeded": True})[0], "FAIL")

    def serve(self, reply):
        path = tempfile.mktemp(prefix="gdj", suffix=".sock", dir="/tmp")
        seen = []

        class H(socketserver.StreamRequestHandler):
            def handle(self_inner):
                seen.append(json.loads(self_inner.rfile.readline()))
                self_inner.wfile.write((json.dumps(reply) + "\n").encode())

        server = socketserver.ThreadingUnixStreamServer(path, H)
        threading.Thread(target=server.serve_forever, daemon=True).start()
        self.addCleanup(lambda: (server.shutdown(), server.server_close(), os.path.exists(path) and os.unlink(path)))
        return path, seen

    def dispatch(self, reply):
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        run_git(root, "init", "-q", "-b", "main")
        (root / "f").write_text("x")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "c")
        request = receiver.validate_request(self.req(expected_sha=head(root)), self.CONTRACT)
        path, seen = self.serve(reply)
        return receiver.dispatch_dev_job(request, root, path), seen, request

    def test_dispatch_forwards_exact_manifest_and_maps_result(self):
        reply = {"ok": True, "request_id": "req_" + "1" * 24, "session": "req_" + "2" * 24, "job_exit": 0,
                 "stdout": "o", "stderr": "", "changed": [], "base_sha": "a" * 40}
        result, seen, request = self.dispatch(reply)
        self.assertEqual(set(seen[0]), {"schema", "id", "repository", "expected_sha", "session", "argv", "timeout_s", "fresh"})
        self.assertEqual(result["read_only"], False)
        self.assertEqual(result["source_sha"], request["expected_sha"])
        self.assertEqual(result["stdout"], "o")

    def test_cross_repo_sha_is_independent_of_servercore_host_sha(self):
        host_sha = "a" * 40
        repo_sha = "b" * 40
        parsed = receiver.validate_request(self.req(repo_sha=repo_sha), self.CONTRACT)
        self.assertEqual(parsed["expected_sha"], host_sha)
        self.assertEqual(parsed["repo_sha"], repo_sha)
        for invalid in ("bad", "z" * 40, 123):
            with self.assertRaises(receiver.ReceiverError):
                receiver.validate_request(self.req(repo_sha=invalid), self.CONTRACT)

        reply = {"ok": True, "request_id": "req_" + "1" * 24, "session": "req_" + "2" * 24,
                 "job_exit": 0, "base_sha": repo_sha}
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        run_git(root, "init", "-q", "-b", "main")
        (root / "f").write_text("x")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "c")
        host_sha = head(root)
        request = receiver.validate_request(self.req(expected_sha=host_sha, repo_sha=repo_sha), self.CONTRACT)
        path, seen = self.serve(reply)
        result = receiver.dispatch_dev_job(request, root, path)
        self.assertEqual(seen[0]["expected_sha"], repo_sha)
        self.assertEqual(result["source_sha"], host_sha)
        self.assertEqual(result["base_sha"], repo_sha)

    def test_dispatch_denials_are_terminal_and_failures_retryable(self):
        with self.assertRaises(receiver.ReceiverError) as ctx:
            self.dispatch({"ok": False, "error": "REPOSITORY_NOT_REGISTERED"})
        self.assertEqual((ctx.exception.code, ctx.exception.status), ("DEV_JOB_DENIED_REPOSITORY_NOT_REGISTERED", 422))
        for error in ("DEV_JOB_BUSY", "INTERNAL_ERROR", "WORKSPACE_CREATE_FAILED"):
            with self.assertRaises(receiver.ReceiverError) as ctx:
                self.dispatch({"ok": False, "error": error})
            self.assertEqual((ctx.exception.code, ctx.exception.status), ("DEV_JOB_EXECUTION_FAILED", 503))
        with self.assertRaises(receiver.ReceiverError) as ctx:
            self.dispatch({"ok": True, "request_id": "req_" + "9" * 24, "session": "req_" + "2" * 24})
        self.assertEqual(ctx.exception.code, "DEV_JOB_RESULT_MISMATCH")
        root = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, root, True)
        run_git(root, "init", "-q", "-b", "main")
        (root / "f").write_text("x")
        run_git(root, "add", "-A")
        run_git(root, "commit", "-q", "-m", "c")
        request = receiver.validate_request(self.req(expected_sha=head(root)), self.CONTRACT)
        with self.assertRaises(receiver.ReceiverError) as ctx:
            receiver.dispatch_dev_job(request, root, "/nonexistent/x.sock")
        self.assertEqual((ctx.exception.code, ctx.exception.status), ("DEV_JOB_EXECUTOR_UNAVAILABLE", 503))
        with self.assertRaises(receiver.bounded_host.BoundaryError):  # stale Host SHA is rejected before the socket
            receiver.dispatch_dev_job({**request, "expected_sha": "b" * 40}, root, "/nonexistent/x.sock")


class SenderWiring(unittest.TestCase):
    CONTRACT = {"request_schema": "gace.servercore-bounded-host.request/v1", "allowed_command_ids": ["dev.job", "project.git_head"]}

    def call(self, **over):
        args = dict(repository="G-ACE-inc/server-core", session="req_" + "2" * 24, argv=["git", "status"],
                    timeout_s=5, fresh=False)
        args.update(over)
        return sender.validate_cli("dev.job", "a" * 40, self.CONTRACT, **args)

    def test_valid_and_invalid_job(self):
        request = self.call()
        self.assertEqual(request["argv"], ["git", "status"])
        self.assertIs(request["fresh"], False)
        for bad in ({"timeout_s": 16}, {"argv": []}, {"fresh": None}, {"session": "x"}, {"repository": None}):
            with self.assertRaises(sender.SendError):
                self.call(**bad)

    def test_target_repository_sha_is_optional_and_validated(self):
        self.assertNotIn("repo_sha", self.call())
        self.assertEqual(self.call(repo_sha="b" * 40)["repo_sha"], "b" * 40)
        for invalid in ("short", "z" * 40, 5):
            with self.assertRaises(sender.SendError):
                self.call(repo_sha=invalid)

    def test_job_fields_rejected_for_other_commands(self):
        with self.assertRaises(sender.SendError):
            sender.validate_cli("project.git_head", "a" * 40, self.CONTRACT, argv=["git"])
        with self.assertRaises(sender.SendError):
            sender.validate_cli("project.git_head", "a" * 40, self.CONTRACT, repository="G-ACE-inc/server-core")


class ContractAndInstallerFiles(unittest.TestCase):
    def test_committed_contract_matches_design_and_registered_projects(self):
        contract = json.loads((ROOT / "operations/github-project-bounded-host.json").read_text())
        policy = contract["dev_job"]
        self.assertEqual(policy["design_section_sha256"],
                         job.design_section_digest((ROOT / "docs/SERVER_CORE_DESIGN.md").read_text(encoding="utf-8")))
        self.assertEqual(set(policy["registered_repositories"]), {"G-ACE-inc/server-core", "seigo-gace/TGserver", "seigo-gace/debug-ai", "seigo-gace/webhook-gateway", "seigo-gace/asteria"})
        self.assertEqual(policy["registered_repositories"]["seigo-gace/TGserver"]["root"], "/home/admin1/projects/TGserver")
        self.assertEqual(policy["registered_repositories"]["seigo-gace/debug-ai"]["root"], "/home/admin1/projects/debug-ai")
        self.assertEqual(policy["allowed_executables"], ["git", "python3", "sh"])
        self.assertEqual(contract["command_effects"]["dev.job"], "dev_job")
        self.assertEqual(policy["registered_repositories"]["G-ACE-inc/server-core"]["branch"], "main")

    def test_unit_has_no_docker_socket_mount_and_runs_as_user(self):
        text = (ROOT / "scripts/servercore_dev_job_host_bootstrap.py").read_text()
        self.assertNotIn("User=root", text)
        self.assertNotIn("docker.sock", (ROOT / "scripts/servercore_dev_job_socket.py").read_text())


class SessionReclamationAtCap(Base):
    """At the session cap only idle, unlocked sessions are reclaimed (oldest first); active work is never evicted."""

    def fill(self, idle_hours):
        base = job.workspace_base(self.root)
        now = time.time()
        names = []
        for i, hours in enumerate(idle_hours):
            path = base / ("req_%024x" % i)
            path.mkdir()
            (path / "work.txt").write_text("edit")
            os.utime(path, (now - hours * 3600, now - hours * 3600))
            names.append(path.name)
        return base, names

    def test_oldest_idle_session_is_reclaimed_to_make_room(self):
        base, names = self.fill([5, 4, 3, 0.1, 0.1, 0.1, 0.1, 0.1])  # 8 live, three idle for hours
        result = self.go(self.request(session="req_" + "e" * 24))
        self.assertEqual(result["job_exit"], 0)
        self.assertFalse((base / names[0]).exists(), "the least recently used idle session is reclaimed")
        for kept in names[1:]:
            self.assertTrue((base / kept).exists(), "only as many as needed are reclaimed")
        self.assertEqual(len([p for p in base.iterdir() if p.is_dir()]), job.MAX_SESSIONS)

    def test_recent_work_is_never_reclaimed(self):
        base, names = self.fill([0.5] * job.MAX_SESSIONS)  # all idle for 30 min < 1 h
        self.denied("SESSION_LIMIT_REACHED", self.request(session="req_" + "e" * 24))
        self.assertTrue(all((base / n).exists() for n in names))

    def test_running_session_is_not_reclaimed_even_when_idle(self):
        base, names = self.fill([5] + [0.1] * (job.MAX_SESSIONS - 1))
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(self.state / (names[0] + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.denied("SESSION_LIMIT_REACHED", self.request(session="req_" + "e" * 24))
        self.assertTrue((base / names[0] / "work.txt").exists())

    def test_ttl_does_not_remove_running_session(self):
        base, names = self.fill([25])
        self.state.mkdir(mode=0o700, parents=True, exist_ok=True)
        fd = os.open(self.state / (names[0] + ".lock"), os.O_CREAT | os.O_RDWR, 0o600)
        self.addCleanup(os.close, fd)
        fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        result = self.go(self.request(session="req_" + "e" * 24))
        self.assertEqual(result["job_exit"], 0)
        self.assertTrue((base / names[0] / "work.txt").exists(),
                        "expired but locked active session must not be removed")

    def test_ttl_prune_and_cap_are_unchanged(self):
        self.assertEqual(job.MAX_SESSIONS, 8)
        self.assertEqual(job.SESSION_TTL_SECONDS, 24 * 3600)
        base, names = self.fill([25])  # beyond the 24 h TTL
        self.go(self.request(session="req_" + "e" * 24))
        self.assertFalse((base / names[0]).exists())

    def test_use_refreshes_the_idle_clock(self):
        self.go()  # creates the session
        workspace = job.workspace_base(self.root) / self.sid
        old = time.time() - 5 * 3600
        os.utime(workspace, (old, old))
        self.go()  # reuse (fresh=false) marks it recently used
        self.assertGreater(workspace.stat().st_mtime, time.time() - 60)


class WorkspaceUnderRestrictiveUmask(unittest.TestCase):
    """Regression: the Host unit runs with UMask=0117; `git clone` then made 0660 directories and failed."""

    def make_repo(self):
        tmp = Path(tempfile.mkdtemp()).resolve()
        self.addCleanup(shutil.rmtree, tmp, ignore_errors=True)
        root = tmp / "repo"
        root.mkdir()
        run_git(root, "init", "-q", "-b", "main")
        (root / "a.txt").write_text("x\n")
        run_git(root, "add", "a.txt")
        run_git(root, "commit", "-q", "-m", "c")
        sha = subprocess.run(["git", "-C", str(root), "rev-parse", "HEAD"], check=True,
                             capture_output=True, text=True).stdout.strip()
        return tmp, root, sha

    def test_workspace_is_created_and_traversable_under_umask_0117(self):
        tmp, root, sha = self.make_repo()
        workspace = tmp / "ws"
        old = os.umask(0o117)
        try:
            job.create_workspace(root, workspace, sha)  # real git clone + checkout + remote remove
        finally:
            os.umask(old)
        self.assertEqual((workspace / "a.txt").read_text(), "x\n")
        for directory in (workspace, workspace / ".git", workspace / ".git" / "objects", workspace / ".git" / "refs"):
            self.assertEqual(os.stat(directory).st_mode & 0o111, 0o111, str(directory))
        self.assertEqual(os.stat(workspace).st_mode & 0o777, 0o755)
        head = subprocess.run(["git", "-C", str(workspace), "-c", "safe.directory=" + str(workspace),
                               "rev-parse", "HEAD"], check=True, capture_output=True, text=True).stdout.strip()
        self.assertEqual(head, sha)

    def test_only_the_git_children_get_the_traversable_umask(self):
        tmp, root, sha = self.make_repo()
        seen = []

        def spy(step, **kwargs):
            seen.append((step[0], kwargs.get("umask")))
            return subprocess.run(step, **kwargs)

        old = os.umask(0o117)
        try:
            job.create_workspace(root, tmp / "ws", sha, runner=spy)
            self.assertEqual(os.umask(0o117), 0o117)  # the process (socket + private state) stays restrictive
        finally:
            os.umask(old)
        self.assertEqual(seen, [("git", 0o022)] * 3)


if __name__ == "__main__":
    unittest.main()
