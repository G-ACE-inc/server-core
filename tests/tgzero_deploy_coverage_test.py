import importlib.util
from pathlib import Path
import unittest

module_path=Path(__file__).resolve().parents[1]/"scripts/tgzero_deploy_coverage.py"
spec=importlib.util.spec_from_file_location("tgzero_coverage",module_path)
m=importlib.util.module_from_spec(spec)
spec.loader.exec_module(m)

class CoverageTests(unittest.TestCase):
    def test_all_registered_projects_are_included_even_without_repo_or_runtime(self):
        s={"projects":{"P001":{"name":"TGS"},"P003":{"name":"personal"},"P009":{"name":"ai-core"}}}
        repo={"repos":{"seigo-gace/TGserver":{"default":"P001"}}}
        containers={"tgserver-tgs-1":"P001","ai-qwen3":"P009"}
        deploy={"repositories":[{"repository":"seigo-gace/TGserver","enabled":True,"revoked":False,"allowed_operations":["reflect"]}]}
        result=m.coverage(s,repo,containers,deploy)
        self.assertEqual(result["total_registered"],3)
        self.assertEqual({x["project_id"] for x in result["rows"]},{"P001","P003","P009"})
        self.assertEqual(result["deploy_authority_mapped"],0)
        self.assertEqual(next(x for x in result["rows"] if x["project_id"]=="P009")["runtime_container_mappings"],["ai-qwen3"])

    def test_registration_not_authorization(self):
        s={"projects":{"P004":{"name":"debug-ai"}}}
        repo={"repos":{"seigo-gace/debug-ai":{"runtime":"P004"}}}
        registry={"repositories":[{"repository":"seigo-gace/debug-ai","enabled":True,"revoked":False,"allowed_operations":["deploy"]}]}
        result=m.coverage(s,repo,{},registry)
        self.assertEqual(result["deploy_authority_mapped"],1)
        self.assertEqual(result["rows"][0]["deploy_coverage"],"AUTHORITY_MAPPED_NOT_HOST_VERIFIED")
        self.assertEqual(result["rows"][0]["repository_mappings"][0]["stream"],"runtime")


    def test_multiple_log_streams_are_one_repo(self):
        s={"projects":{"P004":{"name":"runtime"},"P005":{"name":"kb"}}}
        repo={"repos":{"seigo-gace/debug-ai":{"runtime":"P004","kb":"P005"}}}
        result=m.coverage(s,repo,{},{"repositories":[]})
        self.assertEqual(result["total_registered_log_project_ids"],2)
        self.assertEqual(result["total_repository_mappings"],1)
        self.assertEqual(result["repositories"][0]["project_ids"],["P004","P005"])

if __name__=="__main__":
    unittest.main()
