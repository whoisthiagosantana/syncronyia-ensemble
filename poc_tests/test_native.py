from datetime import timedelta
from pathlib import Path
import unittest
import json
from collections import deque
from unittest.mock import patch

from ensemble_poc.admission import check_quota, utcnow, quota_limit, capacity
from ensemble_poc.contracts import Rejected
from ensemble_poc.planner import plan, STAGES
from ensemble_poc.native import CodexRPC, DISABLED, Native


class NativeTests(unittest.TestCase):
    def readings(self):
        now = utcnow()
        return [
            {
                "scope": s,
                "percent": 12,
                "observed_at": now.isoformat(),
                "resets_at": (now + timedelta(hours=2)).isoformat(),
            }
            for s in ["five_hour", "seven_day"]
        ]

    def test_quota_positive(self):
        self.assertEqual(len(check_quota(self.readings())), 2)

    def test_expiring_owner_exception_preserves_freshness_and_backend_ceiling(self):
        cfg = {
            "owner_quota_exception": {
                "authorized_by": "owner",
                "scope": "functional_poc",
                "expires_at": (utcnow() + timedelta(hours=1)).isoformat(),
                "limit_percent": 100,
            }
        }
        self.assertEqual(quota_limit({}), 35)
        rows = self.readings()
        rows[0]["percent"] = 70
        self.assertEqual(len(check_quota(rows, limit=quota_limit(cfg))), 2)
        rows[0]["percent"] = 100
        with self.assertRaises(Rejected):
            check_quota(rows, limit=quota_limit(cfg))
        cfg["owner_quota_exception"]["expires_at"] = (utcnow() - timedelta(seconds=1)).isoformat()
        with self.assertRaises(Rejected):
            quota_limit(cfg)

    def test_full_integrating_slots_do_not_hide_data_only_observation(self):
        data = {"observed_at": utcnow().isoformat(), "business_hours": True, "live_workers": 2, "worker_limit": 2}
        response = type("Result", (), {"stdout": json.dumps(data).encode()})()
        with patch("ensemble_poc.admission.subprocess.run", return_value=response):
            with self.assertRaisesRegex(Rejected, "GLOBAL_CAPACITY_FULL"):
                capacity("/tmp", ["probe"])
            observed = capacity("/tmp", ["probe"], integrating=False)
        self.assertEqual(observed["live_workers"], 2)
        self.assertEqual(observed["admission_profile"], "tool_free_data_producer")

    def test_quota_negative(self):
        for mutation in [
            lambda r: r.pop(),
            lambda r: r[0].update(percent=35),
            lambda r: r[0].update(percent=True),
            lambda r: r[0].update(percent=float("nan")),
            lambda r: r[0].update(observed_at=(utcnow() - timedelta(minutes=6)).isoformat()),
            lambda r: r[0].update(resets_at=(utcnow() - timedelta(seconds=1)).isoformat()),
        ]:
            r = self.readings()
            mutation(r)
            with self.assertRaises(Rejected):
                check_quota(r)

    def test_real_upstream_nodes_used_without_import(self):
        root = Path(__file__).resolve().parents[1]
        calls = []

        def invoke(provider, prompt, schema):
            calls.append(prompt)
            return {"summary": "bounded", "decisions": [], "risks": []}, {"simulated": True}

        result = plan(root, {"template": "2048", "engine": "ensemble", "intent": "2048"}, invoke)
        self.assertEqual(len(result["stages"]), 3)
        self.assertEqual([c["stage"] for c in calls], [s[0] for s in STAGES])
        self.assertIn("Product Goals", str(calls[0]["planning_nodes"]))
        self.assertEqual(len(calls[2]["previous_stages"]), 2)

    def test_planner_rejects_unsupported_and_bad_output(self):
        root = Path(__file__).resolve().parents[1]
        with self.assertRaises(Rejected):
            plan(root, {"template": "crm", "engine": "ensemble"}, lambda *a: self.fail("called"))
        with self.assertRaises(Rejected):
            plan(
                root, {"template": "2048", "engine": "ensemble", "intent": "2048"}, lambda *a: ({"accepted": True}, {})
            )


class NativeBoundaryTests(unittest.TestCase):
    def test_codex_rejects_tool_start_before_completion(self):
        rpc = object.__new__(CodexRPC)
        rpc.pending = deque()
        rpc.buffer = (
            json.dumps({"method": "item/started", "params": {"item": {"type": "commandExecution"}}}) + "\n"
        ).encode()
        with self.assertRaisesRegex(Rejected, "CODEX_TOOL_EVENT"):
            rpc.read(0)

    def test_missing_auth_and_model_mismatch_never_start_turn(self):
        for authenticated in [False, True]:
            methods = []

            class RPC:
                def __init__(self, *args):
                    pass

                def call(self, method, params):
                    methods.append(method)
                    if method == "account/read":
                        return {"account": {"type": "chatgpt" if authenticated else "apiKey"}}
                    if method == "config/read":
                        return {"config": {"features": {n: False for n in DISABLED}, "web_search": "disabled"}}
                    if method == "account/rateLimits/read":
                        return {
                            "ordinaryUsageAllowed": True,
                            "rateLimitsByLimitId": {
                                "codex": {
                                    "spendControlReached": False,
                                    "primary": {
                                        "windowDurationMins": 10080,
                                        "usedPercent": 1,
                                        "resetsAt": (utcnow() + timedelta(hours=1)).timestamp(),
                                    },
                                }
                            },
                        }
                    if method == "thread/start":
                        return {"model": "unexpected", "modelProvider": "openai"}
                    raise AssertionError("unexpected method")

                def close(self):
                    methods.append("closed")

            cfg = {
                "runtime_root": "/tmp",
                "capacity_probe": [],
                "codex": {
                    "binary": "/usr/bin/true",
                    "auth_file": "/unused",
                    "cli_version": "codex-cli test",
                    "model": "expected",
                    "effective_model": "expected",
                    "required_quota_windows": ["seven_day"],
                },
            }
            with (
                patch("ensemble_poc.native.capacity", return_value={}),
                patch("ensemble_poc.native.bounded", return_value=b"codex-cli test"),
                patch("ensemble_poc.native.CodexRPC", RPC),
            ):
                with self.assertRaises(Rejected):
                    Native(cfg)("codex", {}, None)
            self.assertNotIn("turn/start", methods)
            self.assertEqual(methods[-1], "closed")


if __name__ == "__main__":
    unittest.main()
