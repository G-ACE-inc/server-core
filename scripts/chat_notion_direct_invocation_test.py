import subprocess
import sys
import unittest
from pathlib import Path

SCRIPTS=Path(__file__).resolve().parent
class DirectScriptImportTests(unittest.TestCase):
    def test_ingest_imports_from_scripts_working_directory(self):
        code = (
            "from chat_notion_context_ingest import ingest; "
            "from chat_notion_comment_adapter import parse_comments; "
            "assert ingest([], 'https://github.com/G-ACE-inc/server-core/issues/40') == []"
        )
        result = subprocess.run([sys.executable, "-c", code],
                                cwd=SCRIPTS, capture_output=True, text=True, timeout=15)
        self.assertEqual(result.returncode, 0, result.stderr)

if __name__ == "__main__":
    unittest.main()
