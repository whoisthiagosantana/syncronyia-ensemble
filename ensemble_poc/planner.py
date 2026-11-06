"""Extract MetaGPT's declarative planning nodes without importing executable roles."""

import ast
import copy
import hashlib
from pathlib import Path

from .contracts import GAME_CONTRACT, Rejected, digest
from jsonschema import Draft202012Validator

UPSTREAM = "11cdf466d042aece04fc6cfd13b28e1a70341b1f"
PLAN_SCHEMA = {
    "type": "object",
    "additionalProperties": False,
    "required": ["summary", "decisions", "risks"],
    "properties": {
        "summary": {"type": "string", "maxLength": 4000},
        "decisions": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 1000}},
        "risks": {"type": "array", "maxItems": 20, "items": {"type": "string", "maxLength": 1000}},
    },
}
SOURCE_PINS = {
    "write_prd_an.py": "2e9239a5a0fa64e495e2b4691086d56019c325b1dc3927a749f88b258b5c0902",
    "design_api_an.py": "4d369aab554be580cc9bcb545f6213d0a5afd49e87cfb9c772969b36d75c8409",
    "project_management_an.py": "c2051af8ca148a9358710b62c1e4738d0731a8ef44a10d24682ba3dd26843a11",
}
STAGES = (
    ("requirements", "write_prd_an.py", ("PRODUCT_GOALS", "USER_STORIES", "REQUIREMENT_POOL")),
    ("design", "design_api_an.py", ("IMPLEMENTATION_APPROACH", "FILE_LIST", "ANYTHING_UNCLEAR")),
    ("tasks", "project_management_an.py", ("LOGIC_ANALYSIS", "TASK_LIST", "SHARED_KNOWLEDGE")),
)


def extract(root, filename, names):
    path = Path(root) / "metagpt/actions" / filename
    raw = path.read_bytes()
    if hashlib.sha256(raw).hexdigest() != SOURCE_PINS[filename]:
        raise Rejected("UPSTREAM_SOURCE_CHANGED")
    nodes = {}
    # Only literal fields from selected ActionNode declarations become prompt data.
    for node in ast.parse(raw).body:
        if not isinstance(node, ast.Assign) or not isinstance(node.value, ast.Call):
            continue
        if not isinstance(node.value.func, ast.Name) or node.value.func.id != "ActionNode":
            continue
        for target in node.targets:
            if isinstance(target, ast.Name) and target.id in names:
                fields = {}
                for kw in node.value.keywords:
                    if kw.arg in {"key", "instruction", "example"}:
                        try:
                            fields[kw.arg] = ast.literal_eval(kw.value)
                        except (ValueError, TypeError):
                            pass
                if not {"key", "instruction"} <= fields.keys():
                    raise Rejected("UPSTREAM_NODE_CHANGED")
                nodes[target.id] = fields
    if set(nodes) != set(names):
        raise Rejected("UPSTREAM_NODE_MISSING")
    return {"source": "metagpt/actions/" + filename, "sha256": hashlib.sha256(raw).hexdigest(), "nodes": nodes}


def plan(root, request, invoke):
    if request["template"] != "2048" or request["engine"] != "ensemble":
        raise Rejected("UNSUPPORTED_TEMPLATE_OR_ENGINE")
    results = []
    for stage, filename, names in STAGES:
        instructions = extract(root, filename, names)
        prompt = {
            "stage": stage,
            "intent": request["intent"],
            "fixed_contract": GAME_CONTRACT,
            "upstream": UPSTREAM,
            "planning_nodes": instructions,
            "previous_stages": copy.deepcopy(results),
            "instruction": "Return JSON with summary, decisions, risks. Propose only. The fixed contract overrides upstream examples. Do not invent requirements or perform actions.",
        }
        value, receipt = invoke("claude", prompt, PLAN_SCHEMA)
        if not Draft202012Validator(PLAN_SCHEMA).is_valid(value):
            raise Rejected("PLAN_SCHEMA")
        results.append({"stage": stage, "source": instructions, "proposal": value, "receipt": receipt})
    return {"request": request, "stages": results, "proposal_digest": digest(results)}
