#!/usr/bin/env python3
import hashlib
import importlib.util
import unittest
from pathlib import Path

module_path = Path(__file__).with_name("work_routine_design_entry_gate.py")
spec = importlib.util.spec_from_file_location("design_gate", module_path)
gate = importlib.util.module_from_spec(spec)
spec.loader.exec_module(gate)


def base_rule(**overrides):
    state = dict(
        manifest_verified=True,
        rule_plane_profile="GPT_CHAT",
        rule_plane_read=True,
        current_verified=True,
        purpose_verified=True,
        cu_verified=True,
        purpose_cu_aligned=True,
        mutation_scope="routine_fix",
        design_status="DESIGN_VERIFIED",
        design_adoption="ADOPTED_MAIN",
        implementation_context="adopted_main_implementation",
        source_design_aligned=True,
        claimed_adopted_without_merge=False,
    )
    state.update(overrides)
    return state


class WorkRoutineDesignEntryGateTests(unittest.TestCase):
    def test_rule_entry_pass_and_missing_manifest(self):
        self.assertEqual(gate.evaluate_turn(base_rule()), "PASS")
        self.assertEqual(
            gate.evaluate_turn(base_rule(manifest_verified=False)),
            "RULE_ENTRY_MANIFEST_VERIFIED_NOT_VERIFIED",
        )

    def test_purpose_cu_mismatch_blocks(self):
        self.assertEqual(
            gate.evaluate_turn(base_rule(purpose_cu_aligned=False)),
            "PURPOSE_CU_MISMATCH",
        )

    def test_design_changing_verified_pass(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(
                    mutation_scope="design_changing",
                    design_adoption="ADOPTED_MAIN",
                    implementation_context="adopted_main_implementation",
                )
            ),
            "PASS",
        )

    def test_design_not_found_blocks_changing(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(mutation_scope="design_changing", design_status="DESIGN_NOT_FOUND")
            ),
            "DESIGN_NOT_FOUND_BLOCK",
        )

    def test_design_not_verified_unknown(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(mutation_scope="design_changing", design_status="DESIGN_NOT_VERIFIED")
            ),
            "DESIGN_NOT_VERIFIED_BLOCK",
        )

    def test_unmerged_design_misrepresented(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(
                    mutation_scope="design_changing",
                    design_adoption="PROPOSED_PR",
                    implementation_context="adopted_main_implementation",
                )
            ),
            "DESIGN_NOT_ADOPTED_BLOCK",
        )
        self.assertEqual(
            gate.evaluate_turn(base_rule(claimed_adopted_without_merge=True)),
            "DESIGN_ADOPTION_MISREPRESENTED",
        )

    def test_proposed_pr_staging_allowed(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(
                    mutation_scope="design_changing",
                    design_adoption="PROPOSED_PR",
                    implementation_context="proposed_pr_staging",
                )
            ),
            "PASS",
        )

    def test_design_drift_blocks(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(mutation_scope="design_changing", design_status="DESIGN_DRIFT")
            ),
            "DESIGN_DRIFT_BLOCK",
        )
        self.assertEqual(
            gate.evaluate_turn(base_rule(source_design_aligned=False)),
            "SOURCE_DESIGN_MISMATCH",
        )

    def test_routine_fix_without_new_branch(self):
        self.assertEqual(gate.evaluate_turn(base_rule(mutation_scope="routine_fix")), "PASS")

    def test_consecutive_turns_re_evaluate_rule_entry(self):
        first = base_rule()
        second = base_rule(manifest_verified=False)
        self.assertEqual(gate.evaluate_turn(first), "PASS")
        self.assertNotEqual(gate.evaluate_turn(second), "PASS")

    def test_read_only_skips_design_block(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(
                    mutation_scope="read_only",
                    design_status="DESIGN_NOT_FOUND",
                    manifest_verified=False,
                )
            ),
            "RULE_ENTRY_MANIFEST_VERIFIED_NOT_VERIFIED",
        )
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(mutation_scope="read_only", design_status="DESIGN_NOT_FOUND")
            ),
            "PASS",
        )

    def test_server_ai_profile_rule_entry(self):
        self.assertEqual(
            gate.evaluate_turn(
                base_rule(rule_plane_profile="SERVER_AI", purpose_verified=False)
            ),
            "PASS",
        )




class ReceiptDefaultTrustBoundaryTests(unittest.TestCase):
    def test_emitter_does_not_invent_verified_design(self):
        import importlib.util
        import tempfile
        from unittest.mock import patch

        emitter_path = Path(__file__).with_name("gace_work_routine_turn_receipt.py")
        spec = importlib.util.spec_from_file_location("turn_emitter", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        with tempfile.TemporaryDirectory() as td:
            root = Path(td)
            manifest = root / "operations" / "github-project-rule-plane.json"
            manifest.parent.mkdir()
            manifest.write_text('{"rule_planes":{"server_ai":{"issue_number":16}}}', encoding="utf-8")
            with patch.object(emitter, "gh_issue_body", return_value="fresh rule/current"):
                receipt = emitter.build_receipt(
                    repo_root=root, profile="SERVER_AI",
                    control_repo="G-ACE-inc/server-core", current_issue=40,
                    mutation_scope="routine_fix", design_status="DESIGN_NOT_VERIFIED",
                    purpose_cu_aligned=True,
                )
        self.assertFalse(receipt["source_design_aligned"])
        self.assertEqual(receipt["design_status"], "DESIGN_NOT_VERIFIED")
        self.assertEqual(gate.evaluate_turn(receipt), "SOURCE_DESIGN_MISMATCH")


class WorkRoutineContentHashTests(unittest.TestCase):
    def test_strict_requires_hashes(self):
        import os
        from unittest.mock import patch

        state = base_rule(rule_plane_profile="SERVER_AI", purpose_verified=True)
        with patch.dict(
            os.environ,
            {"GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1", "GACE_WORK_ROUTINE_REPO_ROOT": str(Path(__file__).resolve().parents[1])},
            clear=False,
        ):
            self.assertEqual(gate.evaluate_turn(state), "RULE_ENTRY_EVIDENCE_HASH_REQUIRED")

    def test_manifest_hash_mismatch_denied(self):
        import os
        from unittest.mock import patch

        root = Path(__file__).resolve().parents[1]
        manifest = root / "operations/github-project-rule-plane.json"
        import hashlib

        good = hashlib.sha256(manifest.read_bytes()).hexdigest()
        state = base_rule(
            rule_plane_profile="SERVER_AI",
            purpose_verified=True,
            manifest_sha256=good,
            rule_plane_issue=16,
            current_issue=40,
            rule_plane_body_sha256="deadbeef",
            current_body_sha256="deadbeef",
        )
        with patch.dict(
            os.environ,
            {
                "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
                "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
            },
            clear=False,
        ):
            with patch.object(gate, "gh_issue_body", side_effect=lambda repo, num: f"body-{num}"):
                with patch.object(gate, "manifest_rule_issue", return_value=16):
                    out = gate.evaluate_turn(state)
        self.assertEqual(out, "RULE_ENTRY_RULE_PLANE_HASH_MISMATCH")

    def test_verified_hashes_pass_with_mock_gh(self):
        import os
        from unittest.mock import patch
        import hashlib

        root = Path(__file__).resolve().parents[1]
        manifest = root / "operations/github-project-rule-plane.json"
        manifest_sha = hashlib.sha256(manifest.read_bytes()).hexdigest()
        rule_body = "rule-body-16"
        current_body = "current-body-40"
        state = attach_work_routine_design_baseline(
            base_rule(
                rule_plane_profile="SERVER_AI",
                purpose_verified=True,
                manifest_sha256=manifest_sha,
                rule_plane_issue=16,
                current_issue=40,
                rule_plane_body_sha256=hashlib.sha256(rule_body.encode()).hexdigest(),
                current_body_sha256=hashlib.sha256(current_body.encode()).hexdigest(),
            ),
            root,
        )

        def fake_gh(repo, num):
            return rule_body if num == 16 else current_body

        with patch.dict(
            os.environ,
            {
                "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
                "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
            },
            clear=False,
        ):
            with patch.object(gate, "gh_issue_body", side_effect=fake_gh):
                with patch.object(gate, "manifest_rule_issue", return_value=16):
                    self.assertEqual(gate.evaluate_turn(state), "PASS")



def attach_work_routine_design_baseline(state: dict, root: Path) -> dict:
    doc = (root / "docs/G_ACE_WORKSPACE.md").read_text(encoding="utf-8")
    section = gate.extract_marked_section(
        doc,
        "### Design-alignment checks within the existing Work Routine",
        "## 7. Documentation Gate",
    )
    state = dict(state)
    state.update(
        design_baseline_path="docs/G_ACE_WORKSPACE.md",
        design_baseline_section_id="work_routine_section_6",
        design_baseline_section_sha256=hashlib.sha256(section.encode("utf-8")).hexdigest(),
    )
    return state


class DesignBaselineHashTests(unittest.TestCase):
    def test_strict_design_verified_requires_section_hash(self):
        import os
        from unittest.mock import patch

        root = Path(__file__).resolve().parents[1]
        manifest = root / "operations/github-project-rule-plane.json"
        state = base_rule(
            rule_plane_profile="SERVER_AI",
            purpose_verified=True,
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            rule_plane_issue=16,
            current_issue=40,
            rule_plane_body_sha256=hashlib.sha256(b"body").hexdigest(),
            current_body_sha256=hashlib.sha256(b"body").hexdigest(),
        )
        with patch.dict(
            os.environ,
            {
                "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
                "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
            },
            clear=False,
        ):
            with patch.object(gate, "gh_issue_body", side_effect=lambda repo, num: "body"):
                with patch.object(gate, "manifest_rule_issue", return_value=16):
                    self.assertEqual(
                        gate.evaluate_turn(state),
                        "DESIGN_BASELINE_EVIDENCE_HASH_REQUIRED",
                    )

    def test_design_section_hash_mismatch_denied(self):
        import os
        from unittest.mock import patch

        root = Path(__file__).resolve().parents[1]
        state = attach_work_routine_design_baseline(
            base_rule(rule_plane_profile="SERVER_AI", purpose_verified=True), root
        )
        manifest = root / "operations/github-project-rule-plane.json"
        state.update(
            manifest_sha256=hashlib.sha256(manifest.read_bytes()).hexdigest(),
            rule_plane_issue=16,
            current_issue=40,
            rule_plane_body_sha256=hashlib.sha256(b"body").hexdigest(),
            current_body_sha256=hashlib.sha256(b"body").hexdigest(),
        )
        state["design_baseline_section_sha256"] = "0" * 64
        with patch.dict(
            os.environ,
            {
                "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
                "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
            },
            clear=False,
        ):
            with patch.object(gate, "gh_issue_body", return_value="body"):
                with patch.object(gate, "manifest_rule_issue", return_value=16):
                    self.assertEqual(gate.evaluate_turn(state), "DESIGN_BASELINE_HASH_MISMATCH")

    def test_strict_rejects_noncanonical_design_path(self):
        import os
        from unittest.mock import patch
        root = Path(__file__).resolve().parents[1]
        state = attach_work_routine_design_baseline(base_rule(), root)
        state["design_baseline_path"] = "docs/alternate.md"
        with patch.dict(os.environ, {
            "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
            "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
        }):
            self.assertEqual(
                gate.verify_design_baseline_content_hashes(state),
                "DESIGN_BASELINE_PATH_NOT_CANONICAL",
            )

    def test_emitter_rejects_alternate_baseline_path(self):
        import importlib.util
        from unittest.mock import patch
        path = Path(__file__).with_name("gace_work_routine_turn_receipt.py")
        spec = importlib.util.spec_from_file_location("emitter_path_test", path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        with self.assertRaisesRegex(RuntimeError, "DESIGN_BASELINE_PATH_NOT_CANONICAL"):
            emitter.design_baseline_section_fields(
                Path(__file__).resolve().parents[1],
                "work_routine_section_6", "docs/alternate.md",
            )

    def test_emitter_attaches_verified_section_for_design_verified(self):
        import importlib.util
        import tempfile
        from unittest.mock import patch

        emitter_path = Path(__file__).with_name("gace_work_routine_turn_receipt.py")
        spec = importlib.util.spec_from_file_location("turn_emitter", emitter_path)
        emitter = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(emitter)
        root = Path(__file__).resolve().parents[1]
        with tempfile.TemporaryDirectory() as td:
            out = Path(td) / "turn.json"
            with patch.object(emitter, "gh_issue_body", return_value="fresh"):
                receipt = emitter.build_receipt(
                    repo_root=root,
                    profile="SERVER_AI",
                    control_repo="G-ACE-inc/server-core",
                    current_issue=40,
                    mutation_scope="routine_fix",
                    design_status="DESIGN_VERIFIED",
                    purpose_cu_aligned=True,
                    source_design_aligned=True,
                    design_baseline_section_id="work_routine_section_6",
                )
        self.assertIn("design_baseline_section_sha256", receipt)
        import os
        from unittest.mock import patch

        root = Path(__file__).resolve().parents[1]
        with patch.dict(
            os.environ,
            {
                "GACE_WORK_ROUTINE_REQUIRE_CONTENT_HASH": "1",
                "GACE_WORK_ROUTINE_REPO_ROOT": str(root),
            },
            clear=False,
        ):
            with patch.object(gate, "gh_issue_body", return_value="fresh"):
                with patch.object(gate, "manifest_rule_issue", return_value=16):
                    self.assertEqual(gate.evaluate_turn(receipt), "PASS")

if __name__ == "__main__":
    unittest.main()
