"""Minimal local stdio MCP transport. No shell or configuration operations."""

import json
import sys

from .contracts import Rejected, parse

PROTOCOL = "2024-11-05"
TOOLS = {
    "ensemble_plan": ("Plan a registered 2048 work item", "submit_plan", ["work_item_id", "intent", "request_key"]),
    "ensemble_start": (
        "Start a registered authorized proposal",
        "submit_run",
        ["work_item_id", "plan_id", "request_key"],
    ),
    "ensemble_status": ("Observe an attempt", "status", ["attempt_id"]),
    "ensemble_artifacts": ("List allowed artifact references and digests", "artifacts", ["attempt_id"]),
    "ensemble_cancel": ("Cancel and confirm termination", "cancel", ["attempt_id"]),
}


def dispatch(service, msg):
    method = msg.get("method")
    if method == "initialize":
        version = msg.get("params", {}).get("protocolVersion")
        supported = {PROTOCOL, "2025-03-26", "2025-06-18", "2025-11-25"}
        return {
            "protocolVersion": version if version in supported else PROTOCOL,
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "syncronyia-ensemble-poc", "version": "0.1.0"},
        }
    if method == "ping":
        return {}
    if method == "tools/list":
        return {
            "tools": [
                {
                    "name": name,
                    "description": entry[0],
                    "inputSchema": {
                        "type": "object",
                        "additionalProperties": False,
                        "required": entry[2],
                        "properties": {key: {"type": "string"} for key in entry[2]},
                    },
                }
                for name, entry in TOOLS.items()
            ]
        }
    if method == "tools/call":
        params = msg.get("params", {})
        name = params.get("name")
        if name not in TOOLS:
            raise Rejected("UNKNOWN_TOOL")
        entry = TOOLS[name]
        args = params.get("arguments", {})
        if (
            not isinstance(args, dict)
            or set(args) != set(entry[2])
            or not all(isinstance(v, str) for v in args.values())
        ):
            raise Rejected("INVALID_ARGUMENTS")
        try:
            result = getattr(service, entry[1])(**args)
        except Rejected as exc:
            return {"content": [{"type": "text", "text": str(exc)}], "isError": True}
        return {"content": [{"type": "text", "text": json.dumps(result)}], "isError": False}
    raise Rejected("METHOD_NOT_FOUND")


def serve(service, source=None, sink=None):
    source = source or sys.stdin.buffer
    sink = sink or sys.stdout
    while True:
        line = source.readline(1048577)
        if not line:
            break
        ident = None
        try:
            if len(line) > 1048576:
                while line and not line.endswith(b"\n"):
                    line = source.readline(1048577)
                raise Rejected("REQUEST_LIMIT")
            msg = parse(line, 1048576)
            if not isinstance(msg, dict) or msg.get("jsonrpc") != "2.0":
                raise Rejected("INVALID_REQUEST")
            ident = msg.get("id")
            if "id" not in msg:
                continue
            result = dispatch(service, msg)
            reply = {"jsonrpc": "2.0", "id": ident, "result": result}
        except Rejected as exc:
            reply = {"jsonrpc": "2.0", "id": ident, "error": {"code": -32602, "message": str(exc)}}
        except Exception:
            reply = {"jsonrpc": "2.0", "id": ident, "error": {"code": -32603, "message": "CONTROLLER_UNAVAILABLE"}}
        sink.write(json.dumps(reply) + "\n")
        sink.flush()
