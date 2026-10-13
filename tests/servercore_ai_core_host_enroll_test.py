"""Protect AI Core server-first Host enrollment scope."""
import importlib.util
from pathlib import Path
import unittest
p = Path(__file__).resolve().parents[1] / "scripts/servercore_ai_core_host_enroll.py"
spec=importlib.util.spec_from_file_location("ai_core_host_enroll",p)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
class AICoreHostEnrollmentTests(unittest.TestCase):
    def test_only_existing_isolated_source_checkout(self):
        self.assertEqual(mod.NEW, {"seigo-gace/ai-core":"/home/admin1/projects/ai-core/.worktrees/source-import-20261013"})
        self.assertNotIn("/home/admin1/projects/ai-core", mod.NEW.values())
        self.assertEqual(mod.EXPECTED_DIGEST, "1323b0dc6b3028e6aca6f55c82db4c254084437f3d0b2b43bbb85b928aedcea0")
    def test_denies_unknown_checkout(self):
        with self.assertRaisesRegex(ValueError,"CHECKOUT_NOT_READY"):
            mod.verify_checkout("seigo-gace/ai-core","/missing/source-import")
if __name__=="__main__":
    unittest.main()
