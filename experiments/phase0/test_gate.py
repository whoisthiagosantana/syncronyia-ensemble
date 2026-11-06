"""Contract tests for an untrusted, data-only planning boundary."""

from copy import deepcopy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from gate import InvalidInput, MAX_INPUT_BYTES, ProposalGate, canonical_bytes, digest, load_json
from run_experiment import ROOT, load_fixtures, run_experiment


class ProposalContractTests(unittest.TestCase):
    def setUp(self):
        self.context, self.proposal, _ = load_fixtures()

    def test_fixture_matrix_and_mutations_discriminate(self):
        report = run_experiment()
        self.assertTrue(report["passed"], report)
        self.assertEqual(report["cases_passed"], 28)
        for mutant in report["negative_controls"].values():
            self.assertTrue(mutant["detected"])

    def test_valid_proposal_only_records_a_digest(self):
        gate = ProposalGate(self.context)
        decision = gate.submit(canonical_bytes(self.proposal))
        self.assertEqual(decision.code, "RECORDED")
        self.assertEqual(decision.proposal_sha256, digest(self.proposal))
        self.assertEqual(gate.record_count, 1)

    def test_textual_injection_stays_inert(self):
        with tempfile.TemporaryDirectory() as directory:
            marker = Path(directory) / "should-never-exist"
            self.proposal["assumptions"] = [f"__import__('pathlib').Path({str(marker)!r}).touch()"]
            gate = ProposalGate(self.context)
            self.assertEqual(gate.submit(canonical_bytes(self.proposal)).code, "RECORDED")
            self.assertFalse(marker.exists())

    def test_replay_ignores_json_formatting_and_key_order(self):
        gate = ProposalGate(self.context)
        first = gate.submit(canonical_bytes(self.proposal))
        reversed_keys = dict(reversed(list(self.proposal.items())))
        second = gate.submit(json.dumps(reversed_keys, indent=4))
        self.assertEqual(first.code, "RECORDED")
        self.assertEqual(second.code, "DUPLICATE")
        self.assertEqual(first.proposal_sha256, second.proposal_sha256)
        self.assertEqual(gate.record_count, 1)

    def test_replay_is_explicitly_not_durable(self):
        raw = canonical_bytes(self.proposal)
        self.assertEqual(ProposalGate(self.context).submit(raw).code, "RECORDED")
        self.assertEqual(ProposalGate(self.context).submit(raw).code, "RECORDED")

    def test_rejection_does_not_consume_request(self):
        gate = ProposalGate(self.context)
        invalid = {**self.proposal, "state": "accepted"}
        self.assertEqual(gate.submit(canonical_bytes(invalid)).code, "SCHEMA")
        self.assertEqual(gate.record_count, 0)
        self.assertEqual(gate.submit(canonical_bytes(self.proposal)).code, "RECORDED")

    def test_trusted_context_is_copied(self):
        gate = ProposalGate(self.context)
        self.context["allowed_paths"].append("src/unmanaged.js")
        self.proposal["tasks"][0]["paths"] = ["src/unmanaged.js"]
        self.assertEqual(gate.submit(canonical_bytes(self.proposal)).code, "SCOPE")

    def test_snapshot_covers_every_context_field(self):
        for field in ("allowed_paths", "allowed_evidence_ids", "required_decision_ids"):
            context = deepcopy(self.context)
            context[field].append("NEW-ENTRY" if field != "allowed_paths" else "src/new.js")
            gate = ProposalGate(context)
            self.assertEqual(gate.submit(canonical_bytes(self.proposal)).code, "BINDING", field)

    def test_context_cannot_be_supplied_inside_proposal(self):
        self.proposal["context"] = {**self.context, "allowed_paths": ["secret"]}
        self.assertEqual(ProposalGate(self.context).submit(canonical_bytes(self.proposal)).code, "SCHEMA")

    def test_context_must_satisfy_closed_contract(self):
        for invalid in (None, [], {}, {**self.context, "accepted": True}):
            with self.subTest(invalid=invalid):
                with self.assertRaises(InvalidInput):
                    ProposalGate(invalid)

    def test_noncanonical_paths_fail_even_if_trusted_scope_tries_to_admit_them(self):
        for value in ("../file", "/tmp/file", "src/../file", "src//file", "./src/file", ".git/config", "src\\file", "%2e%2e/file", "."):
            with self.subTest(path=value):
                context = {**self.context, "allowed_paths": [value]}
                with self.assertRaises(InvalidInput):
                    ProposalGate(context)

    def test_dependency_identity_is_unambiguous(self):
        context = {**self.context, "allowed_dependency_ids": [self.context["allowed_task_ids"][0]]}
        with self.assertRaises(InvalidInput):
            ProposalGate(context)

    def test_each_task_evidence_and_self_dependency_are_checked(self):
        for index in (0, 1):
            proposal = deepcopy(self.proposal)
            proposal["tasks"][index]["evidence_refs"] = ["E-UNKNOWN"]
            self.assertEqual(ProposalGate(self.context).submit(canonical_bytes(proposal)).code, "EVIDENCE")
            proposal = deepcopy(self.proposal)
            proposal["tasks"][index]["depends_on"] = [proposal["tasks"][index]["task_id"]]
            self.assertEqual(ProposalGate(self.context).submit(canonical_bytes(proposal)).code, "CYCLE")

    def test_missing_task_and_unknown_nested_fields_are_rejected(self):
        proposal = deepcopy(self.proposal)
        proposal["tasks"].pop()
        self.assertEqual(ProposalGate(self.context).submit(canonical_bytes(proposal)).code, "TASK_IDS")
        self.proposal["tasks"][1]["command"] = "publish"
        self.assertEqual(ProposalGate(self.context).submit(canonical_bytes(self.proposal)).code, "SCHEMA")

    def test_json_limits_and_encoding_are_enforced(self):
        gate = ProposalGate(self.context)
        for raw in (b"x" * (MAX_INPUT_BYTES + 1), b"\xff", "[" * 2000, '"\\ud800"', None, 1):
            with self.subTest(type=type(raw).__name__):
                self.assertIn(gate.submit(raw).code, {"INVALID_JSON", "SCHEMA"})
                self.assertEqual(gate.record_count, 0)

    def test_duplicate_keys_at_any_depth_are_rejected(self):
        for raw in ('{"a":1,"a":2}', '{"tasks":[{"task_id":"A","task_id":"B"}]}'):
            with self.assertRaises(InvalidInput):
                load_json(raw)

    def test_scalar_json_and_wrong_field_types_are_rejected(self):
        gate = ProposalGate(self.context)
        for value in (None, 5, True, [], "string"):
            self.assertEqual(gate.submit(json.dumps(value)).code, "SCHEMA")
        self.proposal["tasks"][0]["paths"] = True
        self.assertEqual(gate.submit(canonical_bytes(self.proposal)).code, "SCHEMA")

    def test_cli_positive_and_rejection_exit_codes(self):
        command = [sys.executable, str(ROOT / "gate.py"), "--context", str(ROOT / "fixtures/context.json"), "--proposal", "-"]
        valid = subprocess.run(command, input=canonical_bytes(self.proposal), capture_output=True, timeout=10)
        self.assertEqual(valid.returncode, 0, valid.stderr)
        self.assertEqual(json.loads(valid.stdout)["code"], "RECORDED")
        self.proposal["state"] = "accepted"
        rejected = subprocess.run(command, input=canonical_bytes(self.proposal), capture_output=True, timeout=10)
        self.assertEqual(rejected.returncode, 1)
        self.assertEqual(json.loads(rejected.stdout)["proposal_records"], 0)

    def test_cli_missing_context_is_generic_and_fail_closed(self):
        command = [sys.executable, str(ROOT / "gate.py"), "--context", str(ROOT / "missing-context.json"), "--proposal", "-"]
        result = subprocess.run(command, input=b"{}", capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 2)
        self.assertEqual(json.loads(result.stdout), {"code": "INVALID_INPUT"})
        self.assertEqual(result.stderr, b"")


if __name__ == "__main__":
    unittest.main()
