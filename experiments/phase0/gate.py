"""Offline proposal validation; no execution, authorization, or durable state."""

from __future__ import annotations

import argparse
from copy import deepcopy
from dataclasses import asdict, dataclass
import hashlib
import json
from pathlib import Path, PurePosixPath
import re
import sys

from jsonschema import Draft202012Validator


MAX_INPUT_BYTES = 65536
SCHEMA = json.loads(Path(__file__).with_name("contract.schema.json").read_text())
Draft202012Validator.check_schema(SCHEMA)
PROPOSAL_VALIDATOR = Draft202012Validator(SCHEMA)
CONTEXT_VALIDATOR = Draft202012Validator(SCHEMA["$defs"]["context"])


class InvalidInput(ValueError):
    """An input is outside the bounded JSON contract."""


def _unique_object(pairs: list[tuple[str, object]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InvalidInput("duplicate JSON key")
        result[key] = value
    return result


def _reject_constant(value: str) -> None:
    raise InvalidInput("non-finite JSON number")


def load_json(raw: bytes | str) -> object:
    """Reject oversized, ambiguous and non-standard JSON without echoing its content."""
    try:
        encoded = raw.encode("utf-8") if isinstance(raw, str) else raw
        if not isinstance(encoded, bytes) or len(encoded) > MAX_INPUT_BYTES:
            raise InvalidInput("input size or type")
        return json.loads(
            encoded.decode("utf-8"),
            object_pairs_hook=_unique_object,
            parse_constant=_reject_constant,
        )
    except (ValueError, UnicodeError, RecursionError) as exc:
        raise InvalidInput("invalid JSON") from exc


def canonical_bytes(value: object) -> bytes:
    return json.dumps(
        value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False
    ).encode("utf-8")


def digest(value: object) -> str:
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def valid_path(value: str) -> bool:
    path = PurePosixPath(value)
    return bool(
        re.fullmatch(r"[A-Za-z0-9_./-]+", value)
        and not path.is_absolute()
        and value == str(path)
        and value != "."
        and ".." not in path.parts
        and ".git" not in path.parts
    )


@dataclass(frozen=True)
class Decision:
    code: str
    proposal_sha256: str | None = None


class ProposalGate:
    """An operator supplies trusted context; model output supplies only a proposal.

    Records live only in this instance. They are not an accepted task, queue item,
    dispatch attempt, resource reservation, or cross-process replay protection.
    """

    def __init__(self, context: dict):
        if not CONTEXT_VALIDATOR.is_valid(context):
            raise InvalidInput("invalid trusted context")
        if any(not valid_path(path) for path in context["allowed_paths"]):
            raise InvalidInput("invalid trusted scope")
        if set(context["allowed_task_ids"]) & set(context["allowed_dependency_ids"]):
            raise InvalidInput("ambiguous dependency identity")
        self._context = deepcopy(context)
        self._snapshot = digest(self._context)
        self._records: dict[str, str] = {}

    @property
    def record_count(self) -> int:
        return len(self._records)

    def _semantic_error(self, proposal: dict) -> str | None:
        context = self._context
        bindings = ("request_id", "work_item_id", "repository_sha", "route", "engine")
        if any(proposal[key] != context[key] for key in bindings):
            return "BINDING"
        if proposal["snapshot_sha256"] != self._snapshot:
            return "BINDING"
        tasks = proposal["tasks"]
        task_ids = [task["task_id"] for task in tasks]
        if len(task_ids) != len(set(task_ids)) or set(task_ids) != set(context["allowed_task_ids"]):
            return "TASK_IDS"
        if set(proposal["open_decisions"]) != set(context["required_decision_ids"]):
            return "DECISIONS"
        allowed_dependencies = set(context["allowed_dependency_ids"]) | set(task_ids)
        for task in tasks:
            if any(not valid_path(path) for path in task["paths"]):
                return "PATH"
            if not set(task["paths"]) <= set(context["allowed_paths"]):
                return "SCOPE"
            if not set(task["depends_on"]) <= allowed_dependencies:
                return "DEPENDENCY"
            if not set(task["evidence_refs"]) <= set(context["allowed_evidence_ids"]):
                return "EVIDENCE"
        graph = {
            task["task_id"]: set(task["depends_on"]) & set(task_ids)
            for task in tasks
        }
        while graph:
            roots = {node for node, dependencies in graph.items() if not dependencies}
            if not roots:
                return "CYCLE"
            graph = {
                node: dependencies - roots
                for node, dependencies in graph.items()
                if node not in roots
            }
        return None

    def _replay_decision(self, request_id: str, proposal_digest: str) -> Decision | None:
        prior = self._records.get(request_id)
        if prior is None:
            return None
        if prior == proposal_digest:
            return Decision("DUPLICATE", prior)
        return Decision("REQUEST_CONFLICT")

    def submit(self, raw: bytes | str) -> Decision:
        try:
            proposal = load_json(raw)
            if not PROPOSAL_VALIDATOR.is_valid(proposal):
                return Decision("SCHEMA")
            error = self._semantic_error(proposal)
            if error:
                return Decision(error)
            proposal_digest = digest(proposal)
        except (InvalidInput, UnicodeError, RecursionError):
            return Decision("INVALID_JSON")
        replay = self._replay_decision(proposal["request_id"], proposal_digest)
        if replay:
            return replay
        self._records[proposal["request_id"]] = proposal_digest
        return Decision("RECORDED", proposal_digest)


def read_bounded(path: str) -> bytes:
    if path == "-":
        return sys.stdin.buffer.read(MAX_INPUT_BYTES + 1)
    with open(path, "rb") as stream:
        return stream.read(MAX_INPUT_BYTES + 1)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--context", required=True, help="Operator-supplied trusted JSON snapshot")
    parser.add_argument("--proposal", required=True, help="Untrusted JSON file, or - for stdin")
    args = parser.parse_args()
    try:
        gate = ProposalGate(load_json(read_bounded(args.context)))
        decision = gate.submit(read_bounded(args.proposal))
    except (InvalidInput, OSError, UnicodeError, RecursionError):
        print(json.dumps({"code": "INVALID_INPUT"}))
        return 2
    print(json.dumps({**asdict(decision), "proposal_records": gate.record_count}))
    return 0 if decision.code == "RECORDED" else 1


if __name__ == "__main__":
    raise SystemExit(main())
