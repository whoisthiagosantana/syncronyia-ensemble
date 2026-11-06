from concurrent.futures import ThreadPoolExecutor
import io
import json
import os
from pathlib import Path
import tempfile
import unittest

from ensemble_poc.contracts import Rejected
from ensemble_poc.mcp import dispatch, serve
from ensemble_poc.service import Service
from ensemble_poc.store import Store
from ensemble_poc.contracts import FILES
from unittest.mock import patch


class LedgerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # The test must fail rather than silently skip persistence evidence.
        cls.dsn = os.environ.get("ENSEMBLE_TEST_DSN")
        if not cls.dsn:
            raise RuntimeError("ENSEMBLE_TEST_DSN must point to a task-scoped PostgreSQL database")
        cls.store = Store(cls.dsn)
        cls.store.initialize()

    def setUp(self):
        with self.store.connect() as c:
            c.execute("TRUNCATE ensemble_poc.events, ensemble_poc.attempts RESTART IDENTITY")

    def test_concurrent_idempotency_survives_new_connection(self):
        def reserve(_):
            return Store(self.dsn).reserve("plan", "WORK-1", "same", {"intent": "2048"})

        with ThreadPoolExecutor(max_workers=8) as ex:
            results = list(ex.map(reserve, range(8)))
        self.assertEqual(len({row[0]["id"] for row in results}), 1)
        self.assertEqual(sum(created for row, created in results), 1)
        with self.assertRaises(Rejected):
            self.store.reserve("plan", "WORK-1", "same", {"intent": "changed"})
        with self.assertRaises(Rejected):
            self.store.reserve("plan", "WORK-2", "other", {})

    def test_unknown_blocks_new_attempt_and_no_automatic_relaunch(self):
        row, _ = self.store.reserve("run", "WORK-1", "key", {})
        self.store.transition(row["id"], ["created"], "unknown")
        row2, created = Store(self.dsn).reserve("run", "WORK-1", "key", {})
        self.assertFalse(created)
        self.assertEqual(row2["state"], "unknown")
        with self.assertRaises(Rejected):
            self.store.reserve("run", "WORK-1", "different", {})
        self.store.transition(row["id"], ["unknown"], "failed")
        self.assertTrue(self.store.reserve("run", "WORK-1", "different", {})[1])

    def test_state_fencing(self):
        row, _ = self.store.reserve("plan", "W", "key", {})
        self.store.transition(row["id"], ["created"], "running")
        with self.assertRaises(Rejected):
            self.store.transition(row["id"], ["created"], "running")
        self.assertEqual(self.store.events(row["id"]), [{"event": "transition", "state": "running"}])

    def test_dispatch_failure_is_durable_unknown(self):
        with tempfile.TemporaryDirectory() as d:

            def fail(_):
                raise OSError("ambiguous")

            svc = Service({"dsn": self.dsn, "runtime_root": d}, launch=fail)
            row = svc._reserve("plan", "W", "key", {})
            self.assertEqual(row["state"], "unknown")
            repeated = svc._reserve("plan", "W", "key", {})
            self.assertTrue(repeated["duplicate"])

    def test_created_status_does_not_race_dispatch_and_replay_needs_no_contract(self):
        with tempfile.TemporaryDirectory() as d:
            svc = Service({"dsn": self.dsn, "runtime_root": d}, launch=lambda _: None)
            value = {"intent": "2048", "template": "2048", "engine": "ensemble", "contract": {}}
            row = svc._reserve("plan", "W", "key", value)
            self.assertEqual(svc.status(row["attempt_id"])["state"], "created")
            replay = svc.submit_plan("W", "2048", "key")
            self.assertTrue(replay["duplicate"])
            with self.assertRaises(Rejected):
                svc.submit_plan("W", "changed", "key")

    def test_simulated_providers_traverse_plan_gate_and_submission(self):
        with tempfile.TemporaryDirectory() as d:
            repo = str(Path(__file__).resolve().parents[1])

            def invoke(provider, prompt, schema):
                if provider == "codex":
                    return {"files": [{"path": f, "content": "synthetic"} for f in FILES]}, {"simulated": True}
                if "stage" in prompt:
                    return {"summary": "bounded", "decisions": [], "risks": []}, {"simulated": True}
                return {"verdict": "PASS", "findings": []}, {"simulated": True}

            svc = Service(
                {"dsn": self.dsn, "runtime_root": d, "repository": repo}, invoke=invoke, launch=lambda _: None
            )
            contract = {
                "work_item_id": "T-GAME-2048",
                "revision_digest": "sha256:synthetic",
                "base_commit": "a" * 40,
                "paths": ["examples/ensemble-2048/" + f for f in FILES],
            }
            svc.contract = lambda _: contract
            planned = svc.submit_plan("T-GAME-2048", "2048", "plan")
            svc.work(planned["attempt_id"])
            self.assertEqual(svc.store.get(planned["attempt_id"])["state"], "planned")
            run = svc.submit_run("T-GAME-2048", planned["attempt_id"].upper(), "run")
            with patch("ensemble_poc.verifier.verify", return_value={"passed": True, "simulated": True}):
                svc.work(run["attempt_id"])
            submitted = svc.store.get(run["attempt_id"])
            self.assertEqual(submitted["state"], "submitted")
            self.assertEqual(submitted["result"]["acceptance"], "pending_external_coordinator")
            self.assertEqual(len(svc.artifacts(run["attempt_id"])["artifacts"]), 5)


class ProtocolTests(unittest.TestCase):
    def test_protocol_and_tool_list(self):
        data = dispatch(None, {"method": "initialize", "params": {"protocolVersion": "2025-11-25"}})
        self.assertEqual(data["protocolVersion"], "2025-11-25")
        tools = dispatch(None, {"method": "tools/list"})["tools"]
        self.assertEqual(len(tools), 5)
        self.assertNotIn("ensemble_accept", [t["name"] for t in tools])

    def test_no_shell_or_extra_arguments(self):
        for args in [{"attempt_id": "id", "shell": "touch /tmp/bad"}, {"attempt_id": 1}]:
            with self.assertRaises(Rejected):
                dispatch(None, {"method": "tools/call", "params": {"name": "ensemble_cancel", "arguments": args}})

    def test_stdio_notification_and_parse_failure(self):
        source = io.BytesIO(
            b'{"jsonrpc":"2.0","method":"notifications/initialized"}\ninvalid\n{"jsonrpc":"2.0","id":3,"method":"ping"}\n'
        )
        sink = io.StringIO()
        serve(None, source, sink)
        replies = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(len(replies), 2)
        self.assertIn("error", replies[0])
        self.assertEqual(replies[1]["result"], {})

    def test_tool_business_failure_is_not_protocol_error(self):
        class Failed:
            def status(self, **kwargs):
                raise Rejected("ATTEMPT_NOT_FOUND")

        reply = dispatch(
            Failed(),
            {"method": "tools/call", "params": {"name": "ensemble_status", "arguments": {"attempt_id": "bad"}}},
        )
        self.assertTrue(reply["isError"])

    def test_oversized_line_does_not_desynchronize(self):
        source = io.BytesIO(b"x" * 1048580 + b"\n" + b'{"jsonrpc":"2.0","id":3,"method":"ping"}\n')
        sink = io.StringIO()
        serve(None, source, sink)
        replies = [json.loads(line) for line in sink.getvalue().splitlines()]
        self.assertEqual(len(replies), 2)
        self.assertEqual(replies[-1]["id"], 3)


if __name__ == "__main__":
    unittest.main()
