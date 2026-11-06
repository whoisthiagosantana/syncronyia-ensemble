"""Exercise synthetic fixtures and kill deliberately broken offline validators."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
from pathlib import Path
from unittest.mock import patch

from gate import Decision, ProposalGate, canonical_bytes, digest


ROOT = Path(__file__).resolve().parent


def load_fixtures() -> tuple[dict, dict, list[dict]]:
    return tuple(
        json.loads((ROOT / "fixtures" / name).read_text())
        for name in ("context.json", "proposal.json", "cases.json")
    )


def run_cases() -> list[dict]:
    original_context, original_proposal, cases = load_fixtures()
    results = []
    for case in cases:
        context, proposal = deepcopy(original_context), deepcopy(original_proposal)
        context.update(case.get("context_set", {}))
        proposal.update(case.get("proposal_set", {}))
        if case.get("rebind_snapshot"):
            proposal["snapshot_sha256"] = digest(context)
        if "task_set" in case:
            mutation = case["task_set"]
            proposal["tasks"][mutation["index"]].update(mutation["values"])
        gate = ProposalGate(context)
        if case.get("repeat"):
            first = gate.submit(canonical_bytes(proposal))
            if first.code != "RECORDED":
                results.append({"id": case["id"], "expected": "RECORDED", "actual": first.code, "pass": False})
                continue
            proposal.update(case.get("after_first_set", {}))
        raw = case["raw"] if "raw" in case else canonical_bytes(proposal)
        decision = gate.submit(raw)
        expected_count = 1 if case["expected"] in {"RECORDED", "DUPLICATE", "REQUEST_CONFLICT"} else 0
        results.append({
            "id": case["id"], "expected": case["expected"], "actual": decision.code,
            "proposal_records": gate.record_count,
            "pass": decision.code == case["expected"] and gate.record_count == expected_count,
        })
    return results


def run_experiment() -> dict:
    results = run_cases()
    mutations = {}
    def always_allow(gate, raw):
        gate._records[gate._context["request_id"]] = "unsafe"
        return Decision("RECORDED")

    broken_methods = {
        "always_allow": ("submit", always_allow),
        "always_reject": ("submit", lambda self, raw: Decision("SCHEMA")),
        "schema_only": ("_semantic_error", lambda self, proposal: None),
        "replay_guard_removed": ("_replay_decision", lambda self, request, proposal_digest: None),
    }
    for name, (method, replacement) in broken_methods.items():
        with patch.object(ProposalGate, method, replacement):
            failed = [case["id"] for case in run_cases() if not case["pass"]]
        mutations[name] = {"detected": bool(failed), "failing_case_ids": failed}
    return {
        "experiment": "EnsemblePhase0/v1alpha1",
        "mode": "offline-synthetic",
        "fixture_sha256": digest(load_fixtures()),
        "cases": results,
        "cases_passed": sum(case["pass"] for case in results),
        "cases_total": len(results),
        "negative_controls": mutations,
        "passed": all(case["pass"] for case in results) and all(item["detected"] for item in mutations.values()),
        "model_calls": 0,
        "implementation_attempts": 0,
        "limits": [
            "No MetaGPT-generated proposal or native executor was exercised.",
            "Proposal records and replay protection exist only within one gate instance.",
            "Reference validity does not prove plan quality, evidence truth or authorization.",
            "Independent provider-diverse review and canonical acceptance remain separate.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="Check without writing a result file")
    parser.add_argument("--output", type=Path, help="Explicit coordinator-selected report destination")
    args = parser.parse_args()
    report = run_experiment()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
