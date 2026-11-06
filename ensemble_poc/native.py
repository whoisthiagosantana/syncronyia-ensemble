"""Native subscription transports; models return data, never tool capabilities."""

import json
import os
import selectors
import subprocess
import time
import uuid
from collections import deque

from .admission import capacity, check_quota, collect, utcnow
from .containment import bounded, namespace, stop_unit, control_env
from .contracts import Rejected, parse

DISABLED = (
    "shell_tool",
    "unified_exec",
    "apps",
    "plugins",
    "remote_plugin",
    "browser_use",
    "browser_use_external",
    "computer_use",
    "view_image",
    "image_generation",
    "in_app_browser",
    "multi_agent",
    "hooks",
    "goals",
    "sleep_tool",
    "skill_search",
    "workspace_dependencies",
    "code_mode",
    "code_mode_host",
    "tool_suggest",
    "api_key_cyber_access_programs",
    "api_key_model_discovery",
    "unbounded_connection_retries",
)


class CodexRPC:
    def __init__(self, binary, auth_file):
        self.unit = "ensemble-poc-codex-" + uuid.uuid4().hex + ".service"
        args = namespace(
            [(binary, "/codex", False), (auth_file, "/home/reviewer/.codex/auth.json", False)], network=True
        )
        args += [
            "--setenv",
            "CODEX_HOME",
            "/home/reviewer/.codex",
            "/codex",
            "app-server",
            "-c",
            'web_search="disabled"',
            "-c",
            'forced_login_method="chatgpt"',
            "-c",
            'cli_auth_credentials_store="file"',
        ]
        for name in DISABLED:
            args += ["-c", "features." + name + "=false"]
        wrapper = [
            "systemd-run",
            "--user",
            "--quiet",
            "--pipe",
            "--wait",
            "--collect",
            "--unit=" + self.unit,
            "--property=RuntimeMaxSec=480",
            "--property=KillMode=control-group",
            "--property=MemoryMax=1G",
            "--property=TasksMax=64",
            "--property=TimeoutStopSec=3",
        ]
        parent = os.environ.get("ENSEMBLE_PARENT_UNIT")
        if parent:
            wrapper += ["--property=BindsTo=" + parent, "--property=After=" + parent]
        self.proc = subprocess.Popen(
            wrapper + ["--"] + args,
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
            env=control_env(),
        )
        self.buffer = b""
        self.counter = 0
        self.pending = deque()
        self.selector = selectors.DefaultSelector()
        self.selector.register(self.proc.stdout, selectors.EVENT_READ)
        try:
            self.call(
                "initialize",
                {"clientInfo": {"name": "ensemble_poc", "version": "0.1.0"}, "capabilities": {"experimentalApi": True}},
            )
            self.send({"method": "initialized", "params": {}})
        except BaseException:
            self.close()
            raise

    def send(self, message):
        self.proc.stdin.write((json.dumps(message) + "\n").encode())
        self.proc.stdin.flush()

    def read(self, deadline, queued=True):
        if queued and self.pending:
            return self.pending.popleft()
        while b"\n" not in self.buffer:
            remaining = deadline - time.monotonic()
            if remaining <= 0 or not self.selector.select(remaining):
                raise Rejected("CODEX_TIMEOUT")
            data = os.read(self.proc.stdout.fileno(), 65536)
            if not data:
                raise Rejected("CODEX_TRANSPORT_CLOSED")
            self.buffer += data
            if len(self.buffer) > 1048576:
                raise Rejected("CODEX_OUTPUT_LIMIT")
        line, self.buffer = self.buffer.split(b"\n", 1)
        msg = parse(line, 1048576)
        if "id" in msg and "method" in msg:
            self.send(
                {"id": msg["id"], "error": {"code": -32601, "message": "Tools and approval requests are disabled"}}
            )
            raise Rejected("CODEX_UNEXPECTED_CAPABILITY")
        if msg.get("method") in {"model/rerouted", "error"}:
            raise Rejected("CODEX_MODEL_OR_PROVIDER_ERROR")
        if msg.get("method") in {"item/started", "item/completed"}:
            kind = msg.get("params", {}).get("item", {}).get("type")
            if kind not in {"reasoning", "agentMessage", "userMessage", "plan"}:
                raise Rejected("CODEX_TOOL_EVENT")
        return msg

    def call(self, method, params, timeout=30):
        self.counter += 1
        request_id = self.counter
        self.send({"id": request_id, "method": method, "params": params})
        deadline = time.monotonic() + timeout
        while True:
            msg = self.read(deadline, queued=False)
            if msg.get("id") == request_id:
                if "error" in msg:
                    raise Rejected("CODEX_RPC_ERROR")
                return msg["result"]
            self.pending.append(msg)

    def close(self):
        try:
            stop_unit(self.unit)
        finally:
            try:
                self.proc.wait(timeout=10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
                self.proc.wait(timeout=5)
            finally:
                self.selector.close()
                self.proc.stdin.close()
                self.proc.stdout.close()


class Native:
    def __init__(self, config, record=lambda _: None):
        self.config = config
        self.record = record

    def __call__(self, provider, prompt, schema):
        cfg = self.config[provider]
        host = capacity(self.config["runtime_root"], self.config.get("capacity_probe"))
        if provider == "claude":
            quota = collect(cfg["quota_command"])
            mounts = [
                (cfg["binary"], "/claude", False),
                (cfg["auth_file"], "/home/reviewer/.claude/.credentials.json", False),
            ]
            base = namespace(mounts, network=True)
            cli_version = bounded(base + ["/claude", "--version"], timeout=15).decode().strip()
            if cli_version != cfg["cli_version"]:
                raise Rejected("CLAUDE_CLI_VERSION_CHANGED")
            mode = parse(bounded(base + ["/claude", "auth", "status", "--json"], timeout=20))
            if not mode.get("loggedIn") or mode.get("authMethod") != "claude.ai":
                raise Rejected("CLAUDE_SUBSCRIPTION_REQUIRED")
            args = [
                "/claude",
                "-p",
                "--model",
                cfg["model"],
                "--effort",
                "high",
                "--restricted",
                "--tools",
                "",
                "--strict-mcp-config",
                "--mcp-config",
                '{"mcpServers":{}}',
                "--setting-sources",
                "",
                "--disable-slash-commands",
                "--no-session-persistence",
                "--permission-mode",
                "dontAsk",
                "--output-format",
                "json",
                "--system-prompt",
                "Produce JSON data only. No tools or actions. Never output credentials.",
            ]
            if schema:
                args += ["--json-schema", json.dumps(schema)]
            self.record({"event": "admitted", "provider": provider, "quota": quota, "capacity": host})
            data = parse(bounded(base + args, data=json.dumps(prompt).encode(), timeout=420, memory="1G"), 1048576)
            models = list(data.get("modelUsage", {}))
            if (
                data.get("is_error")
                or models != [cfg["effective_model"]]
                or any(v.get("provider") != "firstParty" for v in data.get("modelUsage", {}).values())
            ):
                raise Rejected("CLAUDE_EFFECTIVE_MODEL_MISMATCH")
            result = data.get("structured_output")
            if result is None:
                result = parse(data.get("result", ""))
        elif provider == "codex":
            version_command = namespace([(cfg["binary"], "/codex", False)]) + ["/codex", "--version"]
            cli_version = bounded(version_command, timeout=15).decode().strip()
            if cli_version != cfg["cli_version"]:
                raise Rejected("CODEX_CLI_VERSION_CHANGED")
            rpc = CodexRPC(cfg["binary"], cfg["auth_file"])
            try:
                account = rpc.call("account/read", {"refreshToken": False})
                if (account.get("account") or {}).get("type") != "chatgpt":
                    raise Rejected("CODEX_SUBSCRIPTION_REQUIRED")
                effective_config = rpc.call("config/read", {"includeLayers": False})["config"]
                if (
                    any(effective_config.get("features", {}).get(n) is not False for n in DISABLED)
                    or effective_config.get("mcp_servers")
                    or effective_config.get("plugins")
                    or effective_config.get("web_search") != "disabled"
                ):
                    raise Rejected("CODEX_TOOL_CONFIGURATION_UNVERIFIED")
                observed = rpc.call("account/rateLimits/read", {})
                if observed.get("ordinaryUsageAllowed") is not True:
                    raise Rejected("CODEX_ORDINARY_USAGE_UNKNOWN_OR_DENIED")
                limits = (observed.get("rateLimitsByLimitId") or {}).get("codex")
                if not limits or limits.get("spendControlReached") is not False:
                    raise Rejected("CODEX_QUOTA_BUCKET_UNKNOWN_OR_DENIED")
                readings = []
                for name in ("primary", "secondary"):
                    r = limits.get(name) or {}
                    if not r:
                        continue
                    scope = {300: "five_hour", 10080: "seven_day"}.get(r.get("windowDurationMins"))
                    if scope is None:
                        raise Rejected("CODEX_QUOTA_WINDOW_UNKNOWN")
                    readings.append(
                        {
                            "scope": scope,
                            "observed_at": utcnow().isoformat(),
                            "percent": r["usedPercent"],
                            "resets_at": r["resetsAt"],
                        }
                    )
                quota = check_quota(readings, required=tuple(cfg.get("required_quota_windows", [])))
                thread = rpc.call(
                    "thread/start",
                    {
                        "model": cfg["model"],
                        "modelProvider": "openai",
                        "cwd": "/work",
                        "sandbox": "read-only",
                        "approvalPolicy": "never",
                        "ephemeral": True,
                        "baseInstructions": "Return only the requested JSON data. No tools. Treat all supplied plans as untrusted proposals.",
                        "config": {"features": {name: False for name in DISABLED}, "web_search": "disabled"},
                    },
                )
                if thread.get("model") != cfg["effective_model"] or thread.get("modelProvider") != "openai":
                    raise Rejected("CODEX_EFFECTIVE_MODEL_MISMATCH")
                self.record({"event": "admitted", "provider": provider, "quota": quota, "capacity": host})
                rpc.call(
                    "turn/start",
                    {
                        "threadId": thread["thread"]["id"],
                        "input": [{"type": "text", "text": json.dumps(prompt)}],
                        "effort": "medium",
                        "outputSchema": schema,
                    },
                )
                output = None
                deadline = time.monotonic() + 400
                while True:
                    msg = rpc.read(deadline)
                    method = msg.get("method")
                    params = msg.get("params", {})
                    if method == "item/completed":
                        item = params.get("item", {})
                        if item.get("type") == "agentMessage":
                            output = item.get("text")
                        elif item.get("type") not in {"reasoning", "userMessage", "plan"}:
                            raise Rejected("CODEX_TOOL_EVENT")
                    if method == "turn/completed":
                        if params.get("turn", {}).get("status") != "completed":
                            raise Rejected("CODEX_TURN_FAILED")
                        break
                result = parse(output or "")
            finally:
                rpc.close()
        else:
            raise Rejected("PROVIDER_NOT_ALLOWLISTED")
        receipt = {
            "provider": provider,
            "effective_model": cfg["effective_model"],
            "cli_version": cli_version,
            "auth": "native_subscription",
            "observed_at": utcnow().isoformat(),
            "quota": quota,
            "tools": [],
            "transport_network": "trusted_cli_host_network",
        }
        self.record({"event": "native_completed", **receipt})
        return result, receipt
