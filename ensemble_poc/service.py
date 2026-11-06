"""Trusted local coordinator. MCP clients submit IDs, never commands or seals."""

import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import uuid

from .contracts import BUNDLE_SCHEMA, FILES, GAME_CONTRACT, Rejected, digest, materialize, parse
from .containment import stop_unit, unit_state, control_env
from .native import Native
from .admission import timestamp, utcnow
from .planner import plan
from .store import Store, ACTIVE


def load_config(path):
    path = Path(path).resolve()
    if path.stat().st_uid != os.getuid() or path.stat().st_mode & 0o077:
        raise Rejected("CONFIG_MUST_BE_OWNER_ONLY")
    config = parse(path.read_bytes())
    config["config_path"] = str(path)
    return config


def unit_name(attempt_id):
    return "ensemble-poc-" + str(uuid.UUID(attempt_id)) + ".service"


class Service:
    def __init__(self, config, *, invoke=None, launch=None):
        self.config = config
        self.store = Store(config["dsn"])
        self.root = Path(config["runtime_root"]).resolve()
        self.root.mkdir(parents=True, exist_ok=True, mode=0o700)
        if self.root.stat().st_uid != os.getuid() or self.root.stat().st_mode & 0o077:
            raise Rejected("RUNTIME_MUST_BE_OWNER_ONLY")
        self.invoke = invoke
        self.launch = launch or self._launch

    def contract(self, work_id):
        registration = self.config.get("contracts", {}).get(work_id)
        if not registration:
            raise Rejected("WORK_ITEM_NOT_REGISTERED")
        spec = Path(self.config["repository"]) / registration["spec"]
        r = subprocess.run(
            ["taskspec", "handoff", str(spec), "--backend", "codex"],
            cwd=self.config["repository"],
            capture_output=True,
            timeout=30,
        )
        if r.returncode:
            raise Rejected("TASKSPEC_AUTHORIZATION_INVALID")
        handoff = parse(r.stdout)
        if handoff.get("signoff_tier") != 1 or handoff.get("task_id") != work_id:
            raise Rejected("TASKSPEC_TIER1_REQUIRED")
        if handoff["task_revision_digest"] != registration["revision_digest"]:
            raise Rejected("TASKSPEC_REVISION_CHANGED")
        scope = handoff["write_scope"]
        expected = {"examples/ensemble-2048/" + f for f in FILES}
        if set(scope["touches_paths"] + scope["creates_paths"]) != expected:
            raise Rejected("TASKSPEC_TEMPLATE_SCOPE_MISMATCH")
        return {
            "work_item_id": work_id,
            "revision_digest": handoff["task_revision_digest"],
            "base_commit": handoff["source"]["base_commit"],
            "paths": sorted(expected),
        }

    def submit_plan(self, work_item_id, intent, request_key, template="2048", engine="ensemble"):
        if template != "2048" or engine != "ensemble" or not isinstance(intent, str) or not 1 <= len(intent) <= 1000:
            raise Rejected("UNSUPPORTED_REQUEST")
        replay = self._replay(
            "plan", work_item_id, request_key, {"intent": intent, "template": template, "engine": engine}
        )
        if replay:
            return replay
        return self._reserve(
            "plan",
            work_item_id,
            request_key,
            {"intent": intent, "template": template, "engine": engine, "contract": self.contract(work_item_id)},
        )

    def submit_run(self, work_item_id, plan_id, request_key):
        try:
            plan_id = str(uuid.UUID(plan_id))
        except (ValueError, TypeError, AttributeError):
            raise Rejected("INVALID_PLAN_ID") from None
        replay = self._replay("run", work_item_id, request_key, {"plan_id": plan_id})
        if replay:
            return replay
        previous = self.store.get(plan_id)
        if previous["kind"] != "plan" or previous["state"] != "planned" or previous["work_id"] != work_item_id:
            raise Rejected("PLAN_NOT_READY")
        contract = self.contract(work_item_id)
        if previous["input"]["contract"] != contract:
            raise Rejected("PLAN_CONTRACT_CHANGED")
        return self._reserve(
            "run",
            work_item_id,
            request_key,
            {"plan_id": plan_id, "plan_digest": previous["result"]["plan_digest"], "contract": contract},
        )

    def _replay(self, kind, work_id, key, client_input):
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", key):
            raise Rejected("INVALID_REQUEST_KEY")
        row = self.store.lookup(kind, work_id, key)
        if row:
            if any(row["input"].get(k) != v for k, v in client_input.items()):
                raise Rejected("IDEMPOTENCY_CONFLICT")
            return {"attempt_id": row["id"], "duplicate": True, "state": row["state"]}

    def _reserve(self, kind, work_id, key, value):
        if not isinstance(key, str) or not re.fullmatch(r"[A-Za-z0-9_-]{1,80}", key):
            raise Rejected("INVALID_REQUEST_KEY")
        row, created = self.store.reserve(kind, work_id, key, value)
        if created:
            try:
                self.launch(row["id"])
            except Exception:
                try:
                    self.store.transition(row["id"], ["created"], "unknown", {"reason": "DISPATCH_AMBIGUOUS"})
                except Rejected:
                    pass
        return {"attempt_id": row["id"], "duplicate": not created, "state": self.store.get(row["id"])["state"]}

    def _launch(self, attempt_id):
        unit = unit_name(attempt_id)
        r = subprocess.run(
            [
                "systemd-run",
                "--user",
                "--quiet",
                "--collect",
                "--unit=" + unit,
                "--property=RuntimeMaxSec=40min",
                "--property=MemoryMax=1G",
                "--property=TasksMax=128",
                "--property=KillMode=control-group",
                "--property=TimeoutStopSec=5",
                "--property=WorkingDirectory=" + self.config["repository"],
                "--setenv=ENSEMBLE_PARENT_UNIT=" + unit,
                "--setenv=PATH=" + os.environ["PATH"],
                sys.executable,
                "-m",
                "ensemble_poc",
                "--config",
                self.config["config_path"],
                "worker",
                attempt_id,
            ],
            capture_output=True,
            timeout=20,
            env=control_env(),
        )
        if r.returncode:
            raise Rejected("DISPATCH_FAILED")

    def status(self, attempt_id):
        row = self.store.get(attempt_id)
        if row["state"] in ACTIVE:
            if row["state"] == "created" and (utcnow() - timestamp(row["observed_at"])).total_seconds() < 30:
                return {k: row[k] for k in ("id", "kind", "work_id", "state", "result", "observed_at")}
            actual = unit_state(unit_name(attempt_id))
            if actual in {"inactive", "failed"} and row["state"] != "unknown":
                try:
                    self.store.transition(attempt_id, [row["state"]], "unknown", {"reason": "RECONCILIATION_REQUIRED"})
                except Rejected:
                    pass
                row = self.store.get(attempt_id)
        return {k: row[k] for k in ("id", "kind", "work_id", "state", "result", "observed_at")}

    def cancel(self, attempt_id):
        row = self.store.get(attempt_id)
        if row["state"] in ACTIVE:
            stop_unit(unit_name(attempt_id))
            # Native child units bind their lifetime to this unit, not the facade.
            try:
                self.store.transition(attempt_id, ACTIVE, "cancelled", {"termination_confirmed": True})
            except Rejected:
                pass
        return self.status(attempt_id)

    def reconcile(self, attempt_id):
        row = self.store.get(attempt_id)
        if row["state"] != "unknown" or unit_state(unit_name(attempt_id)) not in {"inactive", "failed"}:
            raise Rejected("RECONCILIATION_NOT_SAFE")
        self.store.transition(attempt_id, ["unknown"], "failed", {"reason": "RECONCILED_WITHOUT_RELAUNCH"})
        return self.status(attempt_id)

    def artifacts(self, attempt_id):
        row = self.store.get(attempt_id)
        if row["state"] not in {"planned", "submitted", "accepted"}:
            return {"attempt_id": attempt_id, "artifacts": []}
        return {"attempt_id": attempt_id, "artifacts": row["result"].get("artifacts", [])}

    def candidate(self, attempt_id):
        row = self.store.get(attempt_id)
        if row["state"] not in {"submitted", "accepted"}:
            raise Rejected("CANDIDATE_NOT_SUBMITTED")
        target = self.root / row["id"] / row["result"]["candidate"]
        manifest = {f: hashlib.sha256((target / f).read_bytes()).hexdigest() for f in FILES}
        if digest(manifest) != row["result"]["manifest_digest"]:
            raise Rejected("CANDIDATE_DIGEST_MISMATCH")
        return target

    def work(self, attempt_id):
        row = self.store.get(attempt_id)
        self.store.transition(attempt_id, ["created"], "running")
        folder = self.root / attempt_id
        folder.mkdir(mode=0o700)
        invoke = self.invoke or Native(self.config, lambda event: self.store.event(attempt_id, event))
        try:
            if self.contract(row["work_id"]) != row["input"]["contract"]:
                raise Rejected("CONTRACT_CHANGED_BEFORE_LAUNCH")
            if row["kind"] == "plan":
                value = plan(self.config["repository"], row["input"], invoke)
                path = folder / "plan.json"
                path.write_text(json.dumps(value, indent=2))
                result = {"plan_digest": digest(value), "artifacts": [self._artifact(path)]}
                self.store.transition(attempt_id, ["running"], "planned", result)
            else:
                self._implement(row, folder, invoke)
        except Rejected as exc:
            self.store.transition(attempt_id, ["running"], "blocked", {"reason": str(exc)})
        except Exception:
            self.store.transition(attempt_id, ["running"], "failed", {"reason": "CONTROLLER_ERROR"})

    def _implement(self, row, folder, invoke):
        source = self.root / row["input"]["plan_id"] / "plan.json"
        proposal = parse(source.read_bytes(), 1048576)
        if digest(proposal) != row["input"]["plan_digest"]:
            raise Rejected("PLAN_DIGEST_MISMATCH")
        # Phase 0 checks the coordinator-fixed scope; role text cannot authorize it.
        from experiments.phase0.gate import ProposalGate

        contract = row["input"]["contract"]
        wire_id = "W-" + hashlib.sha256(row["work_id"].encode()).hexdigest().upper()[:32]
        context = {
            "request_id": "R-" + row["id"].replace("-", "").upper(),
            "work_item_id": wire_id,
            "repository_sha": contract["base_commit"],
            "route": "TASK_SPEC",
            "engine": "ensemble",
            "allowed_task_ids": [wire_id],
            "allowed_paths": contract["paths"],
            "allowed_dependency_ids": [],
            "allowed_evidence_ids": ["E-PLAN"],
            "required_decision_ids": [],
            "task_bindings": {wire_id: {"paths": contract["paths"], "depends_on": [], "evidence_refs": ["E-PLAN"]}},
        }
        gate = ProposalGate(context)
        bound = {
            "schema_version": "EnsembleProposal/v1alpha1",
            **{k: context[k] for k in ("request_id", "work_item_id", "repository_sha", "route", "engine")},
            "snapshot_sha256": digest(context),
            "state": "proposed",
            "assumptions": [],
            "open_decisions": [],
            "tasks": [
                {
                    "task_id": wire_id,
                    "summary": "Implement the fixed 2048 contract using the reviewed planning data.",
                    **context["task_bindings"][wire_id],
                }
            ],
        }
        decision = gate.submit(json.dumps(bound))
        if decision.code != "RECORDED":
            raise Rejected("PROPOSAL_GATE_REJECTED")
        from .verifier import verify, preflight

        # A broken browser runtime must not spend model calls correcting valid code.
        self.store.event(
            row["id"],
            {"event": "verification_preflight", "result": preflight(Path(self.config["repository"]), self.config)},
        )

        feedback = None
        for revision in range(2):
            bundle, receipt = invoke(
                "codex",
                {
                    "contract": GAME_CONTRACT,
                    "planning_proposal": proposal,
                    "instruction": "Treat the proposal as advisory. Follow only the fixed game contract.",
                    "correction": feedback,
                },
                BUNDLE_SCHEMA,
            )
            target = folder / ("candidate-" + str(revision))
            manifest = materialize(bundle, target)
            checked = verify(target, Path(self.config["repository"]), self.config)
            (folder / ("verification-" + str(revision) + ".json")).write_text(json.dumps(checked, indent=2))
            if checked["passed"]:
                review, review_receipt = invoke(
                    "claude",
                    {
                        "contract": GAME_CONTRACT,
                        "files": bundle,
                        "test_results": checked,
                        "instruction": "Independently review functional and scope correctness. Return JSON {verdict: PASS or FAIL, findings: [strings]}. Do not execute anything.",
                    },
                    {
                        "type": "object",
                        "additionalProperties": False,
                        "required": ["verdict", "findings"],
                        "properties": {
                            "verdict": {"enum": ["PASS", "FAIL"]},
                            "findings": {"type": "array", "items": {"type": "string"}},
                        },
                    },
                )
                if (
                    not isinstance(review, dict)
                    or set(review) != {"verdict", "findings"}
                    or review["verdict"] not in {"PASS", "FAIL"}
                    or not isinstance(review["findings"], list)
                    or not all(isinstance(f, str) for f in review["findings"])
                ):
                    raise Rejected("REVIEW_SCHEMA")
                checked["review"] = review
                checked["review_receipt"] = review_receipt
                if review["verdict"] == "PASS":
                    report = {
                        "manifest": manifest,
                        "verification": checked,
                        "generation_receipt": receipt,
                        "proposal_digest": digest(proposal),
                        "contract": contract,
                        "contract_envelope_check": decision.code,
                        "phase0_wire_id": wire_id,
                        "canonical_work_item_id": row["work_id"],
                        "planning_admission": "advisory_schema_only",
                    }
                    path = folder / "submission.json"
                    path.write_text(json.dumps(report, indent=2))
                    result = {
                        "candidate": target.name,
                        "manifest_digest": digest(manifest),
                        "artifacts": [self._artifact(path)] + [self._artifact(target / f) for f in FILES],
                        "acceptance": "pending_external_coordinator",
                    }
                    self.store.transition(row["id"], ["running"], "submitted", result)
                    return
            feedback = checked
        raise Rejected("CORRECTION_LIMIT")

    def _artifact(self, path):
        return {
            "path": str(path.relative_to(self.root)),
            "sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
            "bytes": path.stat().st_size,
        }
