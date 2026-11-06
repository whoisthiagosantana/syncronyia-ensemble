"""Exercise synthetic fixtures and kill deliberately broken offline validators."""

from __future__ import annotations

import argparse
from copy import deepcopy
import json
import hashlib
from pathlib import Path
import tempfile
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
        if "append_task" in case:
            proposal["tasks"].append(case["append_task"])
        gate = ProposalGate(context)
        if case.get("repeat"):
            first = gate.submit(canonical_bytes(proposal))
            if first.code != "RECORDED":
                results.append({"id": case["id"], "expected": "RECORDED", "actual": first.code, "pass": False})
                continue
            proposal.update(case.get("after_first_set", {}))
        raw = case["raw"] if "raw" in case else (
            json.dumps(proposal, ensure_ascii=True) if case.get("ascii_json") else canonical_bytes(proposal)
        )
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
        "fixture_sha256": hashlib.sha256(json.dumps(load_fixtures(), sort_keys=True, separators=(",", ":"), ensure_ascii=True).encode("ascii")).hexdigest(),
        "fixture_digest_basis": "ASCII-escaped canonical JSON of the context, proposal and case fixtures.",
        "cases": results,
        "cases_passed": sum(case["pass"] for case in results),
        "cases_total": len(results),
        "negative_controls": mutations,
        "passed": all(case["pass"] for case in results) and all(item["detected"] for item in mutations.values()),
        "declared_model_calls": 0,
        "declared_implementation_attempts": 0,
        "counter_basis": "Declared architectural invariants, not provider or dispatch telemetry.",
        "limits": [
            "No MetaGPT-generated proposal or native executor was exercised.",
            "Proposal records and replay protection exist only within one gate instance.",
            "Reference validity does not prove plan quality, evidence truth or authorization.",
            "Independent provider-diverse review and canonical acceptance remain separate.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument("--check", action="store_true", help="Check without writing a result file")
    mode.add_argument("--output", type=Path, help="Explicit coordinator-selected report destination")
    mode.add_argument("--isolation-probe", action="store_true", help="Run the fixture experiment with bwrap, without network or user home")
    args = parser.parse_args()
    if args.isolation_probe:
        print(json.dumps(isolation_probe(), indent=2, sort_keys=True))
        return 0
    report = run_experiment()
    encoded = json.dumps(report, indent=2, sort_keys=True) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(encoded)
    print(encoded, end="")
    return 0 if report["passed"] else 1


def isolation_probe() -> dict:
    """Reproduce the offline boundary probe; this is not a native-executor sandbox."""
    import importlib.util
    import shutil
    import subprocess

    if not shutil.which("bwrap"):
        raise SystemExit("ISOLATION=UNAVAILABLE bwrap is required")
    with tempfile.TemporaryDirectory(prefix="ensemble-offline-") as directory:
        deps = Path(directory) / "dependencies"
        deps.mkdir()
        for name in ("jsonschema", "jsonschema_specifications", "referencing", "rpds", "attrs", "attr", "typing_extensions"):
            source = Path(importlib.util.find_spec(name).origin)
            if source.name == "__init__.py":
                shutil.copytree(source.parent, deps / name, ignore=shutil.ignore_patterns("__pycache__"))
            else:
                shutil.copy2(source, deps / source.name)
        command = ["bwrap", "--unshare-all", "--die-with-parent", "--new-session"]
        for path in ("/usr", "/lib", "/lib64"):
            if Path(path).exists():
                command.extend(["--ro-bind", path, path])
        command.extend([
            "--proc", "/proc", "--dev", "/dev", "--tmpfs", "/tmp",
            "--ro-bind", str(deps), "/deps", "--ro-bind", str(ROOT), "/experiment",
            "--clearenv", "--setenv", "PATH", "/usr/bin", "--chdir", "/experiment",
            "/usr/bin/python3", "-I", "-S", "-c", _PROBE_CODE,
        ])
        result = subprocess.run(command, capture_output=True, text=True, timeout=30)
        if result.returncode:
            raise SystemExit("ISOLATION=FAILED offline probe did not complete")
        return json.loads(result.stdout)


_PROBE_CODE = """
import json,pathlib,socket,sys
sys.path[:0]=['/deps','/experiment']
from run_experiment import run_experiment
report=run_experiment()
assert report['passed']
assert not pathlib.Path('/home').exists()
pathlib.Path('/tmp/positive').write_text('ok')
assert pathlib.Path('/tmp/positive').read_text()=='ok'
try:
 pathlib.Path('/experiment/forbidden-write').write_text('no')
except OSError:
 readonly=True
else:
 raise AssertionError('experiment mount is writable')
s=socket.socket();s.settimeout(1)
try:
 s.connect(('1.1.1.1',443))
except OSError:
 denied=True
else:
 raise AssertionError('network unexpectedly reachable')
finally:
 s.close()
print(json.dumps({'offline_cases':report['cases_total'],'cases_passed':report['cases_passed'],
 'user_home_absent':True,'experiment_readonly':readonly,'temporary_write_positive':True,
 'external_connection_denied':denied,'native_executor_tested':False}))
"""


if __name__ == "__main__":
    raise SystemExit(main())
