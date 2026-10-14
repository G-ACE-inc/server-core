import importlib.util
from pathlib import Path
import unittest

f=Path(__file__).resolve().parents[1]/"scripts/servercore_service_deploy_admission.py"
spec=importlib.util.spec_from_file_location("service_admission",f)
mod=importlib.util.module_from_spec(spec)
spec.loader.exec_module(mod)
SHA="a"*40
entry={"repository":"seigo-gace/debug-ai","enabled":True,"revoked":False,
       "delegation_mode":"MASTER_INTERNAL_PERSISTENT","allow_production":True,
       "server_project_path":"/home/admin1/projects/debug-ai",
       "allowed_operations":["deploy"],
       "remote":"https://github.com/seigo-gace/debug-ai.git",
       "allowed_branches":["main","master-internal-runtime-20261008"],
       "runtime_target":{"compose_file":"compose.yaml","compose_digest":"a"*64,
                         "services":["debug-ai","sandbox-runner"],"health_service":"debug-ai"}}
def registered(): return {"repositories":[entry.copy()]}


class ServiceAdmissionTests(unittest.TestCase):
    def test_registered_service(self):
        x=mod.require_registered(registered(),"seigo-gace/debug-ai",SHA,"debug-ai")
        self.assertEqual(x["compose_file"],"compose.yaml")

    def test_disallow_unregistered_runtime(self):
        with self.assertRaisesRegex(mod.AdmissionError,"REGISTERED_REPOSITORY_NOT_UNIQUE"):
            mod.require_registered(registered(),"seigo-gace/TGserver",SHA,"tgs")

    def test_source_only_not_deploy(self):
        data=registered()
        data["repositories"][0]["allowed_operations"]=["reflect"]
        with self.assertRaisesRegex(mod.AdmissionError,"DEPLOY_OPERATION_NOT_REGISTERED"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_gateway_api_only_deploy_does_not_expand_docker_access(self):
        data = registered()
        e = data["repositories"][0]
        e["repository"] = "seigo-gace/webhook-gateway"
        e["remote"] = "https://github.com/seigo-gace/webhook-gateway.git"
        e["allowed_operations"] = ["deploy", "docker.operation"]
        e["runtime_target"] = {**entry["runtime_target"],
                               "services": ["api", "worker", "postgres"],
                               "deploy_services": ["api"]}
        x = mod.require_registered(data, "seigo-gace/webhook-gateway", SHA, "api")
        self.assertEqual(x["service"], "api")
        for service in ("worker", "postgres"):
            with self.assertRaisesRegex(mod.AdmissionError, "DEPLOY_SERVICE_NOT_REGISTERED"):
                mod.require_registered(data, "seigo-gace/webhook-gateway", SHA, service)
        read = mod.require_registered(data, "seigo-gace/webhook-gateway", SHA,
                                      "worker", permission="docker.operation")
        self.assertEqual(read["service"], "worker")

    def test_invalid_deploy_services_list_is_denied(self):
        data = registered()
        data["repositories"][0]["runtime_target"] = {
            **entry["runtime_target"], "deploy_services": ["debug-ai", "unregistered"]}
        with self.assertRaisesRegex(mod.AdmissionError, "DEPLOY_SERVICE_NOT_REGISTERED"):
            mod.require_registered(data, "seigo-gace/debug-ai", SHA, "debug-ai")

    def test_no_unregistered_service(self):
        with self.assertRaisesRegex(mod.AdmissionError,"SERVICE_NOT_REGISTERED"):
            mod.require_registered(registered(),"seigo-gace/debug-ai",SHA,"database")

    def test_no_path_escape(self):
        data=registered()
        data["repositories"][0]["server_project_path"]="/home/admin1/projects/../secret"
        with self.assertRaisesRegex(mod.AdmissionError,"HOST_REPOSITORY_PATH_DENIED"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_no_unauthorized_delegation(self):
        data=registered()
        data["repositories"][0]["revoked"]=True
        with self.assertRaisesRegex(mod.AdmissionError,"DELEGATION_DISABLED"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_deny_compose_path_injection(self):
        data=registered()
        data["repositories"][0]["runtime_target"]={**entry["runtime_target"],"compose_file":"../../unsafe.yaml"}
        with self.assertRaisesRegex(mod.AdmissionError,"COMPOSE_PATH_INVALID"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_deny_registered_remote_mismatch(self):
        data=registered()
        data["repositories"][0]["remote"]="https://github.com/other/other.git"
        with self.assertRaisesRegex(mod.AdmissionError,"REGISTERED_REMOTE_INVALID"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_deny_missing_registered_branches(self):
        data=registered()
        data["repositories"][0]["allowed_branches"]=[]
        with self.assertRaisesRegex(mod.AdmissionError,"REGISTERED_BRANCHES_INVALID"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")

    def test_reject_duplicate_registration(self):
        data=registered()
        data["repositories"].append(entry)
        with self.assertRaisesRegex(mod.AdmissionError,"REGISTERED_REPOSITORY_NOT_UNIQUE"):
            mod.require_registered(data,"seigo-gace/debug-ai",SHA,"debug-ai")


if __name__=="__main__": unittest.main()
