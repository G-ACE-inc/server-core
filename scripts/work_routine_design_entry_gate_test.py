#!/usr/bin/env python3
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


if __name__ == "__main__":
    unittest.main()
