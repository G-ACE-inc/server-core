import unittest
from server_core_ci_scope import classify


class ScopeTests(unittest.TestCase):
    def test_server_ai_adapters_and_docs_do_not_require_remote_chat_transport(self):
        result = classify(['AGENTS.md', '.cursor/templates/agents/composer.md', 'docs/LOAD_SCOPE.md',
                           'scripts/workspace_command_center_check.py'])
        self.assertTrue(result['profile_only'])
        self.assertFalse(result['remote_chat'])

    def test_chat_requests_and_notion_implementation_still_require_remote_tests(self):
        for path in ['.github/chat-host-requests/req_example.json', 'scripts/chat_notion_page_evidence.py',
                     'scripts/servercore_bounded_host.py', 'operations/github-project-bounded-host.json']:
            with self.subTest(path=path):
                self.assertTrue(classify(['AGENTS.md', path])['remote_chat'])

    def test_workflow_classifier_changes_unknown_code_and_empty_scope_use_full_ci(self):
        for paths in [[], ['.github/workflows/server-core-guard.yml'], ['scripts/server_core_ci_scope.py'],
                      ['scripts/unrecognized.py'], ['Dockerfile.bounded-host']]:
            self.assertTrue(classify(paths)['remote_chat'])


if __name__ == '__main__':
    unittest.main()
